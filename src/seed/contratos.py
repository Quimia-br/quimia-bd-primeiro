"""Contratos Pydantic por tabela: cada linha passa por aqui antes do insert.

Regras gerais:

- os campos têm os nomes exatos das colunas do DDL; colunas identity (PKs geradas
  pelo banco) não aparecem, porque o seed nunca as envia;
- ``max_length`` igual ao tamanho de cada coluna ``VARCHAR`` (um teste unitário confere);
- campos opcionais (``| None``) exatamente nas colunas que aceitam nulo;
- os valores dos CHECKs do DDL viram enums (``StatusConta``, ``PorteEmpresa``, ``AcaoLog``);
- datas e horas chegam **com fuso** e não podem estar no futuro; a conversão para o
  horário sem fuso das colunas ``TIMESTAMP`` é feita na carga;
- ``extra="forbid"``: um campo com nome errado é erro, não é ignorado.

``comodo`` e ``tipos_historicos.nome`` não têm CHECK no banco: os valores válidos vêm
de ``data/reference`` e são conferidos na leitura dos dados, para mudarem sem código.
"""

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Final, Self
from zoneinfo import ZoneInfo

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from seed import validacao
from seed.config import EMAIL_DOMINIOS, FUSO_DE_GERACAO, IDADE_MINIMA

# ---------------------------------------------------------------------------
# Enums dos CHECKs do DDL (um teste confere contra sql/01_ddl.sql)
# ---------------------------------------------------------------------------


class StatusConta(StrEnum):
    """``chk_status`` de ``usuarios``, ``admins`` e ``usuarios_empresas``."""

    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    PENDENTE = "PENDENTE"
    BLOQUEADO = "BLOQUEADO"
    DESATIVADO = "DESATIVADO"


class PorteEmpresa(StrEnum):
    """``chk_porte`` de ``usuarios_empresas``."""

    PEQUENO = "PEQUENO"
    MEDIO = "MEDIO"
    DESCONHECIDO = "DESCONHECIDO"
    MICRO = "MICRO"
    GRANDE = "GRANDE"


class AcaoLog(StrEnum):
    """``chk_acao`` de ``admin_log_edicoes``."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# ---------------------------------------------------------------------------
# Tipos reutilizáveis
# ---------------------------------------------------------------------------


def _not_in_future(value: datetime) -> datetime:
    if value > datetime.now(UTC):
        msg = "a data não pode estar no futuro"
        raise ValueError(msg)
    return value


def _synthetic_email(value: str) -> str:
    if value != value.lower():
        msg = "o e-mail precisa estar em minúsculas"
        raise ValueError(msg)
    if value.rsplit("@", 1)[-1] not in EMAIL_DOMINIOS:
        msg = f"e-mails sintéticos só podem usar os domínios {sorted(EMAIL_DOMINIOS)}"
        raise ValueError(msg)
    return value


def _valid_json_object(value: str) -> str:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        msg = "dado_anterior precisa ser um JSON válido"
        raise ValueError(msg) from None
    if not isinstance(parsed, dict):
        msg = "dado_anterior precisa ser um objeto JSON (a linha anterior)"
        raise ValueError(msg)
    return value


Id = Annotated[int, Field(gt=0)]
Nome = Annotated[str, Field(min_length=1, max_length=150)]
Email = Annotated[EmailStr, Field(max_length=150), AfterValidator(_synthetic_email)]
SenhaHash = Annotated[str, Field(min_length=1, max_length=255)]
UrlFoto = Annotated[str, AfterValidator(validacao.validar_url_https)]
Momento = Annotated[AwareDatetime, AfterValidator(_not_in_future)]
TextoObrigatorio = Annotated[str, Field(min_length=1)]
Coordenada = Annotated[Decimal, Field(max_digits=9, decimal_places=6)]
Codigo = Annotated[str, Field(min_length=1, max_length=150, pattern=r"^[A-Z][A-Z_]*$")]


class Contrato(BaseModel):
    """Base dos contratos: imutáveis, sem campos extras."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# Tabelas independentes
# ---------------------------------------------------------------------------


class UsuarioEmpresa(Contrato):
    """``usuarios_empresas``."""

    cnpj: Annotated[str, Field(max_length=14), AfterValidator(validacao.validar_cnpj)]
    nome: Nome
    email: Email
    porte: Annotated[PorteEmpresa, Field(max_length=15)]
    data_cadastro: Momento
    senha_hash: SenhaHash
    status: Annotated[StatusConta, Field(max_length=50)]
    url_foto: UrlFoto | None


class Admin(Contrato):
    """``admins``."""

    nome: Nome
    data_cadastro: Momento
    email: Email
    senha_hash: SenhaHash
    status: Annotated[StatusConta, Field(max_length=50)]


class TipoHistorico(Contrato):
    """``tipos_historicos``."""

    nome: Codigo


class Usuario(Contrato):
    """``usuarios``: idade mínima calculada na data de cadastro (fuso de geração)."""

    nome: Nome
    data_nascimento: date | None
    email: Email
    data_cadastro: Momento
    senha_hash: SenhaHash
    status: Annotated[StatusConta, Field(max_length=50)]
    url_foto: UrlFoto | None

    @model_validator(mode="after")
    def _minimum_age(self) -> Self:
        if self.data_nascimento is not None:
            cadastro = self.data_cadastro.astimezone(ZoneInfo(FUSO_DE_GERACAO)).date()
            if validacao.idade_em(self.data_nascimento, cadastro) < IDADE_MINIMA:
                msg = f"o usuário precisa ter pelo menos {IDADE_MINIMA} anos na data de cadastro"
                raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# Tabelas dependentes
# ---------------------------------------------------------------------------


class Produto(Contrato):
    """``produtos``."""

    id_usuario_empresa: Id
    cas_number: Annotated[str, Field(max_length=12), AfterValidator(validacao.validar_cas)]
    nome: Nome
    marca: Nome
    instrucao_de_uso: TextoObrigatorio
    dosagem_tecnica: TextoObrigatorio


class ProdutoUsuario(Contrato):
    """``produtos_usuarios``."""

    id_produto: Id
    id_usuario: Id


class AdminLogEdicao(Contrato):
    """``admin_log_edicoes``: ``dado_anterior`` nulo em INSERT e JSON nos demais."""

    id_admin: Id
    tabela_afetada: Annotated[str, Field(min_length=1, max_length=150)]
    id_registro: Id
    acao: Annotated[AcaoLog, Field(max_length=50)]
    dado_anterior: Annotated[str, AfterValidator(_valid_json_object)] | None
    data_edicao: Momento

    @model_validator(mode="after")
    def _previous_data_by_action(self) -> Self:
        if self.acao is AcaoLog.INSERT and self.dado_anterior is not None:
            msg = "em INSERT, dado_anterior precisa ser nulo"
            raise ValueError(msg)
        if self.acao is not AcaoLog.INSERT and self.dado_anterior is None:
            msg = f"em {self.acao}, dado_anterior precisa trazer a linha anterior"
            raise ValueError(msg)
        return self


class Localizacao(Contrato):
    """``localizacoes``: coordenadas juntas, dentro do Brasil."""

    id_usuario: Id
    cep: Annotated[str, Field(max_length=8), AfterValidator(validacao.validar_cep)]
    latitude: Coordenada | None
    longitude: Coordenada | None

    @model_validator(mode="after")
    def _coordinates(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            msg = "informe latitude e longitude juntas, ou nenhuma das duas"
            raise ValueError(msg)
        if (
            self.latitude is not None
            and self.longitude is not None
            and not validacao.coordenadas_no_brasil(self.latitude, self.longitude)
        ):
            msg = "as coordenadas precisam estar dentro do Brasil"
            raise ValueError(msg)
        return self


class Estante(Contrato):
    """``estantes``."""

    id_usuario: Id
    comodo: Codigo


class Historico(Contrato):
    """``historicos``."""

    id_estante: Id | None
    id_usuario: Id
    id_tipo_historico: Id
    data_execucao: Momento
    descricao_resultado: Annotated[str, Field(min_length=1, max_length=255)] | None


class ProdutoEstante(Contrato):
    """``produtos_estantes``."""

    id_estante: Id
    id_produto: Id
    data_adicao: Momento


class DescarteFds(Contrato):
    """``descartes_fds``: textos de segurança vêm só do catálogo, nunca gerados."""

    id_produto: Id
    metodo_descarte_produto: TextoObrigatorio | None
    metodo_descarte_embalagem: TextoObrigatorio | None
    restricao_descarte: TextoObrigatorio | None
    precaucao_ambiental: TextoObrigatorio | None


class HistoricoProduto(Contrato):
    """``historicos_produtos``."""

    id_produto: Id
    id_historico: Id
    id_usuario: Id


CONTRATOS: Final[dict[str, type[Contrato]]] = {
    "usuarios_empresas": UsuarioEmpresa,
    "admins": Admin,
    "tipos_historicos": TipoHistorico,
    "usuarios": Usuario,
    "produtos": Produto,
    "produtos_usuarios": ProdutoUsuario,
    "admin_log_edicoes": AdminLogEdicao,
    "localizacoes": Localizacao,
    "estantes": Estante,
    "historicos": Historico,
    "produtos_estantes": ProdutoEstante,
    "descartes_fds": DescarteFds,
    "historicos_produtos": HistoricoProduto,
}
"""Contrato de cada tabela, pelo nome da tabela no banco."""
