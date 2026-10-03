"""Diagnóstico somente leitura do banco, usado pelo ``seed check``."""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import Connection, String, column, select, table, text

from seed.config import Settings
from seed.db.engine import create_db_engine
from seed.db.table_names import EXPECTED_TABLES

_SERVER_QUERY = text(
    """
    SELECT current_database()                         AS database,
           current_user                               AS usuario,
           current_schema()                           AS schema_atual,
           current_setting('server_version')          AS server_version,
           current_setting('max_connections')::int    AS max_connections,
           current_setting('TimeZone')                AS timezone,
           pg_database_size(current_database())       AS database_size,
           (SELECT count(*)
              FROM pg_stat_activity
             WHERE datname = current_database())      AS open_connections
    """
)

# information_schema só lista tabelas sobre as quais o usuário tem algum privilégio.
_TABLES_QUERY = text(
    """
    SELECT table_name
      FROM information_schema.tables
     WHERE table_schema = :schema
       AND table_type = 'BASE TABLE'
    """
)


@dataclass(frozen=True, slots=True)
class ServerInfo:
    """Resultado do diagnóstico."""

    database: str
    user: str
    current_schema: str | None
    server_version: str
    max_connections: int
    open_connections: int
    database_size_bytes: int
    timezone: str
    alembic_revision: str | None
    missing_tables: tuple[str, ...]


def collect_server_info(
    conn: Connection,
    schema: str,
    expected_tables: Iterable[str] = EXPECTED_TABLES,
) -> ServerInfo:
    """Lê versão, limites, tamanho, fuso, revisão do Alembic e tabelas existentes."""
    row = conn.execute(_SERVER_QUERY).mappings().one()
    existing = set(conn.execute(_TABLES_QUERY, {"schema": schema}).scalars())
    revision = _alembic_revision(conn, schema) if "alembic_version" in existing else None
    return ServerInfo(
        database=row["database"],
        user=row["usuario"],
        current_schema=row["schema_atual"],
        server_version=row["server_version"],
        max_connections=row["max_connections"],
        open_connections=row["open_connections"],
        database_size_bytes=row["database_size"],
        timezone=row["timezone"],
        alembic_revision=revision,
        missing_tables=tuple(sorted(set(expected_tables) - existing)),
    )


def fetch_server_info(settings: Settings) -> ServerInfo:
    """Abre uma conexão, coleta o diagnóstico e libera o pool."""
    engine = create_db_engine(settings)
    try:
        with engine.connect() as conn:
            return collect_server_info(conn, settings.db_schema)
    finally:
        engine.dispose()


def _alembic_revision(conn: Connection, schema: str) -> str | None:
    version_table = table("alembic_version", column("version_num", String), schema=schema)
    revisions = conn.execute(select(version_table.c.version_num)).scalars().all()
    return ", ".join(sorted(revisions)) or None
