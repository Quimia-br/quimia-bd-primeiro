"""Montagem da URL e da engine do SQLAlchemy para os bancos do Aiven."""

from typing import Final, Literal

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL

from seed.config import ConfigError, Settings

type Role = Literal["seed", "migration"]
"""Quem conecta: o seed ou as migrações (Alembic). Sem credencial própria, as
migrações usam a mesma do seed (ADR 0014)."""

APPLICATION_NAMES: Final[dict[Role, str]] = {
    "seed": "quimia-seed",
    "migration": "quimia-seed-migracao",
}


def build_url(settings: Settings, role: Role = "seed") -> URL:
    """URL ``postgresql+psycopg`` com SSL. A senha nunca aparece em ``str(url)``."""
    user, password = settings.db_user, settings.db_password
    if (
        role == "migration"
        and settings.migration_db_user is not None
        and settings.migration_db_password is not None
    ):
        user, password = settings.migration_db_user, settings.migration_db_password

    return URL.create(
        drivername="postgresql+psycopg",
        username=user,
        password=password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        query={
            "sslmode": settings.db_sslmode,
            "sslrootcert": str(settings.db_sslrootcert),
        },
    )


def connect_args(settings: Settings, role: Role = "seed") -> dict[str, object]:
    """Parâmetros extras do psycopg: nome da aplicação, timeout e ``search_path``."""
    return {
        "application_name": APPLICATION_NAMES[role],
        "connect_timeout": settings.db_connect_timeout,
        # db_schema já foi validado como identificador simples em Settings.
        "options": f"-c search_path={settings.db_schema}",
    }


def create_db_engine(settings: Settings, role: Role = "seed") -> Engine:
    """Cria a engine com pool pequeno e ``pool_pre_ping``. Não abre conexão ainda."""
    if not settings.db_sslrootcert.is_file():
        msg = (
            f"Arquivo do CA não encontrado: {settings.db_sslrootcert}. "
            "Baixe o certificado CA do serviço no console do Aiven e salve em certs/."
        )
        raise ConfigError(msg)
    return create_engine(
        build_url(settings, role),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        connect_args=connect_args(settings, role),
    )
