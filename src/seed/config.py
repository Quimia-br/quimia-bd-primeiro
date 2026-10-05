"""Configuração do seed: alvos, conexão, quantidades e formatos de URL.

Cada alvo tem o seu arquivo na pasta de onde o comando é executado: ``.env.test``
para o banco de teste e ``.env`` para o principal. Variáveis de ambiente reais têm
prioridade sobre o arquivo. Todos os campos usam o prefixo ``SEED_``.

As mensagens de erro deste módulo nunca exibem valores: só os nomes das variáveis.
"""

import ipaddress
import os
import re
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import dotenv_values
from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL

ENV_PREFIX: Final = "SEED_"
TARGET_ENV_VAR: Final = "SEED_TARGET"
REDACTED: Final = "***"
APPLICATION_NAME: Final = "quimia-seed"

# ---------------------------------------------------------------------------
# Quantidades da carga (fixas; altere aqui). tipos_historicos não aparece porque
# recebe exatamente os tipos de data/reference.
# ---------------------------------------------------------------------------
QUANTIDADE_PADRAO: Final = 100
QUANTIDADES: Final[dict[str, int]] = {
    "usuarios_empresas": QUANTIDADE_PADRAO,
    "admins": QUANTIDADE_PADRAO,
    "usuarios": QUANTIDADE_PADRAO,
    "produtos": QUANTIDADE_PADRAO,
    "admin_log_edicoes": QUANTIDADE_PADRAO,
    "localizacoes": QUANTIDADE_PADRAO,  # 1:1 com usuarios
    "estantes": QUANTIDADE_PADRAO,
    "produtos_usuarios": QUANTIDADE_PADRAO,
    "descartes_fds": QUANTIDADE_PADRAO,  # 1 por produto
    "produtos_estantes": QUANTIDADE_PADRAO,
    "historicos": QUANTIDADE_PADRAO,
    "historicos_produtos": QUANTIDADE_PADRAO,
}
SEMENTE_PADRAO: Final = 42
# Pasta data/ do projeto (reference/ e catalog/). O projeto é instalado em modo
# editável pelo uv, então o caminho é relativo ao código-fonte.
DATA_DIR: Final = Path(__file__).resolve().parents[2] / "data"
IDADE_MINIMA: Final = 18
FRACAO_SEM_DATA_NASCIMENTO: Final = 0.10
FUSO_DE_GERACAO: Final = "America/Sao_Paulo"
# Cadastros sorteados nos últimos N dias antes do momento da carga.
JANELA_CADASTRO_DIAS: Final = 3 * 365
# Pesos do status das contas (usuarios, admins, usuarios_empresas).
PESOS_STATUS: Final = {
    "ATIVO": 80,
    "INATIVO": 8,
    "PENDENTE": 5,
    "BLOQUEADO": 4,
    "DESATIVADO": 3,
}
FRACAO_CNPJ_ALFANUMERICO: Final = 0.3
FRACAO_LOCALIZACAO_COM_COORDENADAS: Final = 0.9
FRACAO_HISTORICO_SEM_DESCRICAO: Final = 0.2
IDADE_MAXIMA: Final = 80
# Domínios reservados para exemplos (RFC 2606): e-mails sintéticos nunca são reais.
EMAIL_DOMINIOS: Final = frozenset({"example.com", "example.org"})

# ---------------------------------------------------------------------------
# Fotos (troque o serviço aqui, sem mexer nos geradores).
# ---------------------------------------------------------------------------
FOTO_USUARIO: Final = "https://randomuser.me/api/portraits/{genero}/{indice}.jpg"
FOTO_USUARIO_GENEROS: Final = {"feminino": "women", "masculino": "men"}
FOTO_USUARIO_INDICES: Final = range(100)
FOTO_EMPRESA: Final = "https://ui-avatars.com/api/?name={nome}&size=256"

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class Target(StrEnum):
    """Banco de destino da carga."""

    TEST = "test"
    MAIN = "main"

    @property
    def env_file_name(self) -> str:
        """Nome do arquivo de configuração do alvo (o principal usa o ``.env``)."""
        return ".env" if self is Target.MAIN else f".env.{self.value}"


class ConfigError(Exception):
    """Configuração ausente ou inválida. A mensagem nunca contém valores secretos."""


class Settings(BaseSettings):
    """Configuração de um alvo."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    target: Target = Target.TEST

    db_host: str = Field(min_length=1)
    db_port: int = Field(gt=0, lt=65536)
    db_user: str = Field(min_length=1)
    db_password: SecretStr
    db_name: str = Field(min_length=1)
    db_schema: str = "public"
    # verify-ca por padrão: o libpq do psycopg-binary no Windows rejeita o IPv6 do
    # certificado do Aiven com verify-full (ver README, Decisões).
    db_sslmode: Literal["verify-full", "verify-ca"] = "verify-ca"
    db_sslrootcert: Path
    db_pool_size: int = Field(default=2, ge=1, le=10)
    db_max_overflow: int = Field(default=1, ge=0, le=10)
    db_connect_timeout: int = Field(default=10, ge=1, le=120)

    timezone: str = "UTC"
    password_plain: SecretStr | None = None

    @field_validator("db_schema")
    @classmethod
    def _check_schema(cls, value: str) -> str:
        if not _IDENTIFIER.fullmatch(value):
            msg = "use só letras minúsculas, dígitos e '_' (identificador simples do Postgres)"
            raise ValueError(msg)
        return value

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError, ValueError:
            msg = "fuso horário desconhecido; use um nome IANA, como 'UTC' ou 'America/Sao_Paulo'"
            raise ValueError(msg) from None
        return value

    @property
    def zone(self) -> ZoneInfo:
        """Fuso usado para gravar as colunas TIMESTAMP sem fuso."""
        return ZoneInfo(self.timezone)

    @property
    def masked_host(self) -> str:
        """Host mascarado, seguro para exibir."""
        return mask_host(self.db_host)

    def redact(self, text: str) -> str:
        """Remove host, endereços IP e senhas de um texto (por exemplo, mensagens de erro)."""
        for secret in (self.db_password, self.password_plain):
            if secret is not None and secret.get_secret_value():
                text = text.replace(secret.get_secret_value(), REDACTED)
        text = text.replace(self.db_host, self.masked_host)
        return _IPV4.sub(REDACTED, text)


def mask_host(host: str) -> str:
    """Mascara um host: ``pg-quimia.example.com`` vira ``pg-***.example.com``."""
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return REDACTED
    labels = host.split(".")
    first = f"{labels[0][:3]}{REDACTED}"
    if len(labels) <= 2:
        return first
    return ".".join([first, *labels[-2:]])


def resolve_target(value: str | None = None) -> Target:
    """Resolve o alvo: valor explícito, depois ``SEED_TARGET``, depois ``test``."""
    raw = value if value is not None else os.environ.get(TARGET_ENV_VAR, Target.TEST.value)
    try:
        return Target(raw.strip().lower())
    except ValueError:
        msg = f"Alvo inválido: {raw!r}. Use 'test' ou 'main'."
        raise ConfigError(msg) from None


def load_settings(target: Target, env_dir: Path | None = None) -> Settings:
    """Carrega a configuração do alvo a partir do arquivo do alvo e do ambiente."""
    directory = env_dir or Path.cwd()
    env_file = directory / target.env_file_name
    try:
        settings = Settings(
            _env_file=env_file if env_file.is_file() else None,
            target=target,
        )
    except ValidationError as exc:
        # ``from None``: a ValidationError original inclui os valores recebidos.
        raise ConfigError(_describe_errors(exc, target, env_file)) from None
    if target is Target.TEST:
        _ensure_test_is_not_main(settings, directory / Target.MAIN.env_file_name)
    return settings


@lru_cache(maxsize=2)
def get_settings(target: Target | None = None) -> Settings:
    """Configuração do alvo, carregada uma vez por processo (os testes usam ``cache_clear``)."""
    return load_settings(target if target is not None else resolve_target())


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------


def build_url(settings: Settings) -> URL:
    """URL ``postgresql+psycopg`` com SSL. A senha nunca aparece em ``str(url)``."""
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        query={
            "sslmode": settings.db_sslmode,
            "sslrootcert": str(settings.db_sslrootcert),
        },
    )


def connect_args(settings: Settings) -> dict[str, object]:
    """Parâmetros extras do psycopg: nome da aplicação, timeout e ``search_path``."""
    return {
        "application_name": APPLICATION_NAME,
        "connect_timeout": settings.db_connect_timeout,
        # db_schema já foi validado como identificador simples em Settings.
        "options": f"-c search_path={settings.db_schema}",
    }


def create_db_engine(settings: Settings) -> Engine:
    """Cria a engine com pool pequeno e ``pool_pre_ping``. Não abre conexão ainda."""
    if not settings.db_sslrootcert.is_file():
        msg = (
            f"Arquivo do CA não encontrado: {settings.db_sslrootcert}. "
            "Baixe o certificado CA do serviço no console do Aiven e salve em certs/."
        )
        raise ConfigError(msg)
    return create_engine(
        build_url(settings),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        connect_args=connect_args(settings),
    )


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def _ensure_test_is_not_main(settings: Settings, main_env_file: Path) -> None:
    """Aborta se o alvo test resolveu para o mesmo servidor configurado no ``.env``.

    O ``.env`` é carregado automaticamente por várias ferramentas (por exemplo, a
    extensão Python do Cursor/VS Code). Se as variáveis dele forem injetadas no
    ambiente, elas teriam prioridade sobre o ``.env.test`` e o alvo test apontaria
    para o banco principal sem aviso.
    """
    if not main_env_file.is_file():
        return
    main = dotenv_values(main_env_file)
    main_host = (main.get(f"{ENV_PREFIX}DB_HOST") or "").strip().lower()
    main_port = (main.get(f"{ENV_PREFIX}DB_PORT") or "").strip()
    if main_host == settings.db_host.strip().lower() and main_port == str(settings.db_port):
        msg = (
            "O alvo test está apontando para o mesmo servidor do banco principal "
            f"(configurado em {main_env_file.name}). Confira SEED_DB_HOST e SEED_DB_PORT "
            f"no {Target.TEST.env_file_name} e se há variáveis SEED_* definidas no ambiente "
            "(o editor pode carregar o .env automaticamente)."
        )
        raise ConfigError(msg)


def _describe_errors(exc: ValidationError, target: Target, env_file: Path) -> str:
    origin = env_file.name if env_file.is_file() else f"{env_file.name} não encontrado"
    lines = [f"Configuração inválida para o alvo '{target}' ({origin}):"]
    for error in exc.errors(include_input=False, include_url=False):
        field = str(error["loc"][0]) if error["loc"] else ""
        name = f"{ENV_PREFIX}{field.upper()}" if field else "configuração"
        detail = "obrigatória e não definida" if error["type"] == "missing" else error["msg"]
        lines.append(f"  - {name}: {detail}")
    return "\n".join(lines)
