"""Modelos ORM que espelham ``sql/01_ddl.sql`` e ``sql/02_fks.sql`` (fonte da verdade).

Os modelos NÃO criam nem alteram tabelas: o schema é gerenciado fora deste projeto
pelos scripts de ``sql/``. Eles servem para descrever as tabelas, dar a ordem de
carga e a tipagem. Os inserts usam o Core (``insert(Modelo.__table__)``).

Regras deste arquivo:

- nomes de tabelas, colunas e constraints exatamente como no DDL;
- colunas na mesma ordem do DDL;
- CHECKs com o mesmo texto do DDL;
- PKs simples como ``GENERATED ALWAYS AS IDENTITY``: o banco recusa IDs informados,
  então o seed nunca envia essas colunas e obtém os IDs com ``RETURNING``.

Qualquer mudança no DDL exige atualizar ``sql/``, este arquivo e ``contratos.py``
juntos. O ``seed check`` compara estes modelos com o banco real.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Final

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Integer,
    MetaData,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# As constraints que o DDL nomeia (chk_*, fk_*) recebem o nome direto nos modelos.
# As sem nome (PKs e UNIQUEs) recebem do Postgres os nomes abaixo, que a convenção
# reproduz: <tabela>_pkey e <tabela>_<colunas>_key.
NAMING_CONVENTION: Final = {
    "pk": "%(table_name)s_pkey",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
}


class Base(DeclarativeBase):
    """Base de todos os modelos."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


_NOW = text("CURRENT_TIMESTAMP")
_UNKNOWN = text("'DESCONHECIDO'")

_CHECK_STATUS = "status IN ('ATIVO', 'INATIVO', 'PENDENTE','BLOQUEADO', 'DESATIVADO')"
_CHECK_URL_FOTO = "url_foto LIKE 'http://%' OR url_foto LIKE 'https://%'"


def _identity_pk() -> Mapped[int]:
    return mapped_column(Integer, Identity(always=True), primary_key=True)


# ================================
# TABELAS INDEPENDENTES
# ================================


class CompanyUser(Base):
    """``usuarios_empresas``: empresas donas dos produtos."""

    __tablename__ = "usuarios_empresas"
    __table_args__ = (
        CheckConstraint(
            "porte IN ('PEQUENO', 'MEDIO', 'DESCONHECIDO', 'MICRO', 'GRANDE')",
            name="chk_porte",
        ),
        CheckConstraint(_CHECK_URL_FOTO, name="chk_url_foto"),
        CheckConstraint(_CHECK_STATUS, name="chk_status"),
    )

    id_usuario_empresa: Mapped[int] = _identity_pk()
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    porte: Mapped[str] = mapped_column(String(15), server_default=_UNKNOWN)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime(), server_default=_NOW)
    senha_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    url_foto: Mapped[str | None] = mapped_column(Text)


class Admin(Base):
    """``admins``: administradores do app."""

    __tablename__ = "admins"
    __table_args__ = (CheckConstraint(_CHECK_STATUS, name="chk_status"),)

    id_admin: Mapped[int] = _identity_pk()
    nome: Mapped[str] = mapped_column(String(150))
    data_cadastro: Mapped[datetime] = mapped_column(DateTime(), server_default=_NOW)
    email: Mapped[str] = mapped_column(String(150), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))


class HistoryType(Base):
    """``tipos_historicos``: tabela de referência dos tipos de histórico."""

    __tablename__ = "tipos_historicos"

    id_tipo_historico: Mapped[int] = _identity_pk()
    nome: Mapped[str] = mapped_column(String(150), unique=True)


class User(Base):
    """``usuarios``: usuários finais do app."""

    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(_CHECK_STATUS, name="chk_status"),
        CheckConstraint(_CHECK_URL_FOTO, name="chk_url_foto"),
    )

    id_usuario: Mapped[int] = _identity_pk()
    nome: Mapped[str] = mapped_column(String(150))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str] = mapped_column(String(150), unique=True)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime(), server_default=_NOW)
    senha_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    url_foto: Mapped[str | None] = mapped_column(Text)


# ============================
# TABELAS DEPENDENTES
# ============================


class Product(Base):
    """``produtos``: um produto por CAS (``cas_number`` é UNIQUE; ver pauta, item 1)."""

    __tablename__ = "produtos"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_usuario_empresa"],
            ["usuarios_empresas.id_usuario_empresa"],
            name="fk_produto_usuario_empresa",
        ),
    )

    id_produto: Mapped[int] = _identity_pk()
    id_usuario_empresa: Mapped[int] = mapped_column(Integer)
    cas_number: Mapped[str] = mapped_column(String(12), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    marca: Mapped[str] = mapped_column(String(150), server_default=_UNKNOWN)
    instrucao_de_uso: Mapped[str] = mapped_column(Text)
    dosagem_tecnica: Mapped[str] = mapped_column(Text)


class UserProduct(Base):
    """``produtos_usuarios``: produtos que cada usuário possui."""

    __tablename__ = "produtos_usuarios"
    __table_args__ = (
        PrimaryKeyConstraint("id_usuario", "id_produto"),
        ForeignKeyConstraint(
            ["id_usuario"], ["usuarios.id_usuario"], name="fk_produto_usuario_usuario"
        ),
        ForeignKeyConstraint(
            ["id_produto"], ["produtos.id_produto"], name="fk_produto_usuario_produto"
        ),
    )

    id_produto: Mapped[int] = mapped_column(Integer)
    id_usuario: Mapped[int] = mapped_column(Integer)


class AdminEditLog(Base):
    """``admin_log_edicoes``: auditoria de edições feitas por admins."""

    __tablename__ = "admin_log_edicoes"
    __table_args__ = (
        CheckConstraint("acao IN ('INSERT', 'UPDATE', 'DELETE')", name="chk_acao"),
        ForeignKeyConstraint(["id_admin"], ["admins.id_admin"], name="fk_admin_log_edicao_admin"),
    )

    id_admin_log_edicao: Mapped[int] = _identity_pk()
    id_admin: Mapped[int] = mapped_column(Integer)
    tabela_afetada: Mapped[str] = mapped_column(String(150))
    id_registro: Mapped[int] = mapped_column(Integer)
    acao: Mapped[str] = mapped_column(String(50))
    dado_anterior: Mapped[str | None] = mapped_column(Text)
    data_edicao: Mapped[datetime] = mapped_column(DateTime(), server_default=_NOW)


class Location(Base):
    """``localizacoes``: uma localização por usuário (``id_usuario`` UNIQUE)."""

    __tablename__ = "localizacoes"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_longitude"),
        ForeignKeyConstraint(
            ["id_usuario"], ["usuarios.id_usuario"], name="fk_localizacao_usuario"
        ),
    )

    id_localizacao: Mapped[int] = _identity_pk()
    id_usuario: Mapped[int] = mapped_column(Integer, unique=True)
    cep: Mapped[str] = mapped_column(String(8))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))


class Shelf(Base):
    """``estantes``: no máximo uma estante por cômodo de cada usuário."""

    __tablename__ = "estantes"
    __table_args__ = (
        # Alvo da FK composta de historicos (estante do mesmo usuário).
        UniqueConstraint("id_estante", "id_usuario"),
        UniqueConstraint("id_usuario", "comodo"),
        ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], name="fk_estante_usuario"),
    )

    id_estante: Mapped[int] = _identity_pk()
    id_usuario: Mapped[int] = mapped_column(Integer)
    comodo: Mapped[str] = mapped_column(String(150), server_default=_UNKNOWN)


class History(Base):
    """``historicos``: ações do usuário (uso, mistura, descarte...)."""

    __tablename__ = "historicos"
    __table_args__ = (
        # Alvo da FK composta de historicos_produtos (mesmo usuário do histórico).
        UniqueConstraint("id_historico", "id_usuario"),
        ForeignKeyConstraint(
            ["id_tipo_historico"],
            ["tipos_historicos.id_tipo_historico"],
            name="fk_historico_tipo_historico",
        ),
        ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], name="fk_historico_usuario"),
        # MATCH SIMPLE: com id_estante nulo, a FK não é verificada.
        ForeignKeyConstraint(
            ["id_estante", "id_usuario"],
            ["estantes.id_estante", "estantes.id_usuario"],
            name="fk_historico_estante",
        ),
    )

    id_historico: Mapped[int] = _identity_pk()
    id_estante: Mapped[int | None] = mapped_column(Integer)
    id_usuario: Mapped[int] = mapped_column(Integer)
    id_tipo_historico: Mapped[int] = mapped_column(Integer)
    data_execucao: Mapped[datetime] = mapped_column(DateTime(), server_default=_NOW)
    descricao_resultado: Mapped[str | None] = mapped_column(String(255))


class ShelfProduct(Base):
    """``produtos_estantes``: produtos guardados em cada estante."""

    __tablename__ = "produtos_estantes"
    __table_args__ = (
        PrimaryKeyConstraint("id_estante", "id_produto"),
        ForeignKeyConstraint(
            ["id_estante"], ["estantes.id_estante"], name="fk_produto_estante_estante"
        ),
        ForeignKeyConstraint(
            ["id_produto"], ["produtos.id_produto"], name="fk_produto_estante_produto"
        ),
    )

    id_estante: Mapped[int] = mapped_column(Integer)
    id_produto: Mapped[int] = mapped_column(Integer)
    data_adicao: Mapped[datetime] = mapped_column(DateTime(), server_default=_NOW)


# ==========================
# TABELA FDS
# ==========================


class SdsDisposal(Base):
    """``descartes_fds``: um registro de descarte por produto (``id_produto`` UNIQUE)."""

    __tablename__ = "descartes_fds"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_produto"], ["produtos.id_produto"], name="fk_descarte_fds_produto"
        ),
    )

    id_descarte_fds: Mapped[int] = _identity_pk()
    id_produto: Mapped[int] = mapped_column(Integer, unique=True)
    metodo_descarte_produto: Mapped[str | None] = mapped_column(Text)
    metodo_descarte_embalagem: Mapped[str | None] = mapped_column(Text)
    restricao_descarte: Mapped[str | None] = mapped_column(Text)
    precaucao_ambiental: Mapped[str | None] = mapped_column(Text)


# ===========================
# TABELA ASSOCIATIVA
# ===========================


class HistoryProduct(Base):
    """``historicos_produtos``: produtos envolvidos em cada histórico."""

    __tablename__ = "historicos_produtos"
    __table_args__ = (
        UniqueConstraint("id_historico", "id_produto"),
        ForeignKeyConstraint(
            ["id_historico", "id_usuario"],
            ["historicos.id_historico", "historicos.id_usuario"],
            name="fk_historico_produto_historico",
        ),
        ForeignKeyConstraint(
            ["id_usuario", "id_produto"],
            ["produtos_usuarios.id_usuario", "produtos_usuarios.id_produto"],
            name="fk_historico_produto_produto_usuario",
        ),
    )

    id_historico_produto: Mapped[int] = _identity_pk()
    id_produto: Mapped[int] = mapped_column(Integer)
    id_historico: Mapped[int] = mapped_column(Integer)
    id_usuario: Mapped[int] = mapped_column(Integer)


# ===========================
# ORDEM DE CARGA
# ===========================


def table_levels(metadata: MetaData = Base.metadata) -> dict[str, int]:
    """Nível de cada tabela: 1 para as sem dependências; senão 1 + o maior nível dos pais.

    Tabelas do mesmo nível não dependem umas das outras.
    """
    levels: dict[str, int] = {}
    for table in metadata.sorted_tables:  # garante os pais antes dos filhos
        parents = {fk.column.table.name for fk in table.foreign_keys} - {table.name}
        levels[table.name] = 1 + max((levels[parent] for parent in parents), default=0)
    return levels


def load_order(metadata: MetaData = Base.metadata) -> list[str]:
    """Tabelas em ordem de carga (por nível e, dentro do nível, pela ordem topológica)."""
    levels = table_levels(metadata)
    return sorted(levels, key=lambda name: levels[name])


def table_names(metadata: MetaData = Base.metadata) -> frozenset[str]:
    """Nomes de todas as tabelas dos modelos."""
    return frozenset(metadata.tables)
