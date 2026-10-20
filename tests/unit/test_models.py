"""Conferências dos modelos contra o DDL que não precisam de banco.

A comparação completa (tipos, defaults, CHECKs normalizados, FKs) é feita pelo teste
de paridade de integração; aqui ficam as conferências estruturais, lendo os scripts.
"""

import re

from seed.modelos import Base, load_order, table_levels
from tests.conftest import SQL_DIR

DDL = (SQL_DIR / "01_ddl.sql").read_text(encoding="utf-8")
FKS = (SQL_DIR / "02_fks.sql").read_text(encoding="utf-8")

_CREATE = re.compile(r"CREATE TABLE (\w+)\s*\((.*?)\n\s*\);", re.DOTALL)
_NOT_A_COLUMN = ("CONSTRAINT", "UNIQUE", "PRIMARY", "FOREIGN", "CHECK")


def _ddl_columns() -> dict[str, list[str]]:
    tables: dict[str, list[str]] = {}
    for name, body in _CREATE.findall(DDL):
        columns = []
        for raw in body.splitlines():
            line = raw.strip()
            if line and not line.startswith(_NOT_A_COLUMN):
                columns.append(line.split()[0])
        tables[name] = columns
    return tables


def test_tables_match_ddl() -> None:
    assert set(Base.metadata.tables) == set(_ddl_columns())
    assert len(Base.metadata.tables) == 13


def test_columns_match_ddl_in_order() -> None:
    for name, columns in _ddl_columns().items():
        assert [c.name for c in Base.metadata.tables[name].columns] == columns, name


def test_named_checks_match_ddl() -> None:
    expected = {
        (table, check)
        for table, body in _CREATE.findall(DDL)
        for check in re.findall(r"CONSTRAINT (\w+) CHECK", body)
    }
    actual = {
        (table.name, str(constraint.name))
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert actual == expected


def test_foreign_keys_match_fks_sql() -> None:
    pattern = re.compile(
        r"ALTER TABLE (\w+) ADD CONSTRAINT (\w+)\s+FOREIGN KEY \(([^)]*)\)\s+"
        r"REFERENCES (\w+) \(([^)]*)\)"
    )

    def cols(raw: str) -> tuple[str, ...]:
        return tuple(c.strip() for c in raw.split(","))

    expected = {
        (table, name, cols(local), referent, cols(remote))
        for table, name, local, referent, remote in pattern.findall(FKS)
    }
    actual = {
        (
            table.name,
            str(fk.name),
            tuple(fk.column_keys),
            fk.referred_table.name,
            tuple(element.column.name for element in fk.elements),
        )
        for table in Base.metadata.tables.values()
        for fk in table.foreign_key_constraints
    }
    assert len(expected) == 14
    assert actual == expected


def test_identity_always_on_simple_primary_keys() -> None:
    for table in Base.metadata.tables.values():
        pk = list(table.primary_key.columns)
        if len(pk) == 1:
            identity = pk[0].identity
            assert identity is not None, table.name
            assert identity.always is True, table.name


def test_unnamed_constraints_get_postgres_default_names() -> None:
    names = {str(c.name) for t in Base.metadata.tables.values() for c in t.constraints}

    assert "usuarios_pkey" in names
    assert "produtos_usuarios_pkey" in names
    assert "usuarios_empresas_cnpj_key" in names
    assert "estantes_id_estante_id_usuario_key" in names
    assert "historicos_produtos_id_historico_id_produto_key" in names


def test_load_levels() -> None:
    expected = {
        1: {"usuarios_empresas", "admins", "tipos_historicos", "usuarios"},
        2: {"produtos", "admin_log_edicoes", "localizacoes", "estantes"},
        3: {"produtos_usuarios", "descartes_fds", "produtos_estantes", "historicos"},
        4: {"historicos_produtos"},
    }
    levels = table_levels()

    for level, tables in expected.items():
        assert {name for name, value in levels.items() if value == level} == tables


def test_load_order_puts_parents_first() -> None:
    order = load_order()
    for table in Base.metadata.tables.values():
        for fk in table.foreign_keys:
            assert order.index(fk.column.table.name) < order.index(table.name)
