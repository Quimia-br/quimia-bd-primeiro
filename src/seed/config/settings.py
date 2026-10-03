"""Configuração do seed por alvo (``test`` ou ``main``).

Cada alvo tem o seu arquivo (``.env.test`` ou ``.env.main``) na pasta de onde o
comando é executado. Variáveis de ambiente reais têm prioridade sobre o arquivo.
Todos os campos usam o prefixo ``SEED_`` (por exemplo, ``SEED_DB_HOST``).

As mensagens de erro desta camada nunca exibem valores: só os nomes das variáveis.
"""

import ipaddress
import os
import re
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX: Final = "SEED_"
TARGET_ENV_VAR: Final = "SEED_TARGET"
REDACTED: Final = "***"

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class Target(StrEnum):
    """Banco de destino da carga."""

    TEST = "test"
    MAIN = "main"

    @property
    def env_file_name(self) -> str:
        """Nome do arquivo de configuração do alvo."""
        return f".env.{self.value}"


class ConfigError(Exception):
    """Configuração ausente ou inválida. A mensagem nunca contém valores secretos."""


class Settings(BaseSettings):
    """Configuração completa de um alvo."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    target: Target = Target.TEST

    # Conexão do seed (usuário definido no .env, ADR 0014).
    db_host: str = Field(min_length=1)
    db_port: int = Field(gt=0, lt=65536)
    db_user: str = Field(min_length=1)
    db_password: SecretStr
    db_name: str = Field(min_length=1)
    db_schema: str = "public"
    db_sslmode: Literal["verify-full", "verify-ca"] = "verify-full"
    db_sslrootcert: Path
    db_pool_size: int = Field(default=2, ge=1, le=10)
    db_max_overflow: int = Field(default=1, ge=0, le=10)
    db_connect_timeout: int = Field(default=10, ge=1, le=120)

    # Credencial opcional das migrações. Sem ela, o Alembic usa a mesma do seed.
    migration_db_user: str | None = None
    migration_db_password: SecretStr | None = None

    # Carga.
    batch_size: int = Field(default=1000, ge=1, le=50_000)
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

    @model_validator(mode="after")
    def _check_target_rules(self) -> Self:
        if self.target is Target.MAIN and self.password_plain is not None:
            msg = "SEED_PASSWORD_PLAIN só pode ser definida no alvo test"
            raise ValueError(msg)
        if (self.migration_db_user is None) != (self.migration_db_password is None):
            msg = "defina SEED_MIGRATION_DB_USER e SEED_MIGRATION_DB_PASSWORD juntas"
            raise ValueError(msg)
        return self

    @property
    def zone(self) -> ZoneInfo:
        """Fuso usado para gravar as colunas TIMESTAMP sem fuso (ADR 0010)."""
        return ZoneInfo(self.timezone)

    @property
    def masked_host(self) -> str:
        """Host mascarado, seguro para exibir."""
        return mask_host(self.db_host)

    def redact(self, text: str) -> str:
        """Remove host, endereços IP e senhas de um texto (por exemplo, mensagens de erro)."""
        secrets = [self.db_password, self.migration_db_password, self.password_plain]
        for secret in secrets:
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
    """Carrega a configuração do alvo a partir do ``.env.<alvo>`` e do ambiente."""
    env_file = (env_dir or Path.cwd()) / target.env_file_name
    try:
        return Settings(
            _env_file=env_file if env_file.is_file() else None,
            target=target,
        )
    except ValidationError as exc:
        # ``from None``: a ValidationError original inclui os valores recebidos.
        raise ConfigError(_describe_errors(exc, target, env_file)) from None


@lru_cache(maxsize=2)
def get_settings(target: Target | None = None) -> Settings:
    """Configuração do alvo, carregada uma vez por processo (os testes usam ``cache_clear``)."""
    return load_settings(target if target is not None else resolve_target())


def _describe_errors(exc: ValidationError, target: Target, env_file: Path) -> str:
    origin = env_file.name if env_file.is_file() else f"{env_file.name} não encontrado"
    lines = [f"Configuração inválida para o alvo '{target}' ({origin}):"]
    for error in exc.errors(include_input=False, include_url=False):
        field = str(error["loc"][0]) if error["loc"] else ""
        name = f"{ENV_PREFIX}{field.upper()}" if field else "configuração"
        detail = "obrigatória e não definida" if error["type"] == "missing" else error["msg"]
        lines.append(f"  - {name}: {detail}")
    return "\n".join(lines)
