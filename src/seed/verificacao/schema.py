"""Comparação dos modelos ORM com as tabelas reais do banco (somente leitura).

Usada pelo ``seed check`` (mostra as divergências) e pelo ``seed run`` (recusa a carga
se houver alguma). Compara, por reflexão: tabelas, colunas, tipos, nulidade, PKs,
UNIQUEs e FKs. Defaults e CHECKs não entram: o Postgres reescreve o texto deles, e os
CHECKs já são conferidos contra o DDL nos testes unitários.
"""

from typing import Any

from sqlalchemy import Connection, MetaData, Table, UniqueConstraint, inspect
from sqlalchemy.dialects import postgresql

from seed.modelos import Base

_DIALECT = postgresql.dialect()


def _tipo(tipo: Any) -> str:
    return str(tipo.compile(dialect=_DIALECT))


def _unicos_do_modelo(tabela: Table) -> set[tuple[str, ...]]:
    unicos = {
        tuple(c.name for c in constraint.columns)
        for constraint in tabela.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    unicos |= {(c.name,) for c in tabela.columns if c.unique}
    return unicos


def _fks_do_modelo(tabela: Table) -> set[tuple[tuple[str, ...], str, tuple[str, ...]]]:
    return {
        (
            tuple(fk.column_keys),
            fk.referred_table.name,
            tuple(e.column.name for e in fk.elements),
        )
        for fk in tabela.foreign_key_constraints
    }


def comparar_schema(conn: Connection, schema: str, metadata: MetaData = Base.metadata) -> list[str]:
    """Divergências entre os modelos e o banco; lista vazia quando batem."""
    inspector = inspect(conn)
    existentes = set(inspector.get_table_names(schema=schema))
    divergencias: list[str] = []

    for nome, tabela in sorted(metadata.tables.items()):
        if nome not in existentes:
            divergencias.append(f"{nome}: tabela não existe no banco")
            continue

        reais = {c["name"]: c for c in inspector.get_columns(nome, schema=schema)}
        for coluna in tabela.columns:
            real = reais.pop(coluna.name, None)
            if real is None:
                divergencias.append(f"{nome}.{coluna.name}: coluna não existe no banco")
                continue
            if _tipo(coluna.type) != _tipo(real["type"]):
                divergencias.append(
                    f"{nome}.{coluna.name}: tipo {_tipo(real['type'])} no banco, "
                    f"{_tipo(coluna.type)} no modelo"
                )
            if bool(coluna.nullable) != bool(real["nullable"]):
                no_banco = "aceita" if real["nullable"] else "não aceita"
                divergencias.append(f"{nome}.{coluna.name}: no banco {no_banco} nulo")
        for sobra in sorted(reais):
            divergencias.append(f"{nome}.{sobra}: coluna existe no banco, mas não no modelo")

        pk_real = tuple(inspector.get_pk_constraint(nome, schema=schema)["constrained_columns"])
        pk_modelo = tuple(c.name for c in tabela.primary_key.columns)
        if set(pk_real) != set(pk_modelo):
            divergencias.append(f"{nome}: PK {pk_real} no banco, {pk_modelo} no modelo")

        unicos_reais = {
            tuple(u["column_names"]) for u in inspector.get_unique_constraints(nome, schema=schema)
        }
        unicos_reais |= {
            tuple(str(c) for c in i["column_names"])
            for i in inspector.get_indexes(nome, schema=schema)
            if i["unique"]
        }
        for faltando in sorted(_unicos_do_modelo(tabela) - unicos_reais):
            divergencias.append(f"{nome}: UNIQUE {faltando} não existe no banco")

        fks_reais = {
            (tuple(f["constrained_columns"]), f["referred_table"], tuple(f["referred_columns"]))
            for f in inspector.get_foreign_keys(nome, schema=schema)
        }
        for fk in sorted(_fks_do_modelo(tabela) - fks_reais):
            divergencias.append(f"{nome}: FK {fk[0]} -> {fk[1]}{fk[2]} não existe no banco")
        for fk in sorted(fks_reais - _fks_do_modelo(tabela)):
            divergencias.append(f"{nome}: FK {fk[0]} -> {fk[1]}{fk[2]} existe só no banco")

    return divergencias
