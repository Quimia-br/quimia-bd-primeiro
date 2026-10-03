"""Nomes das 13 tabelas de ``sql/01_ddl.sql``.

Provisório: na Fase 3 esta lista passa a vir de ``Base.metadata``.
"""

from typing import Final

EXPECTED_TABLES: Final = frozenset(
    {
        "usuarios_empresas",
        "admins",
        "tipos_historicos",
        "usuarios",
        "produtos",
        "produtos_usuarios",
        "admin_log_edicoes",
        "localizacoes",
        "estantes",
        "historicos",
        "produtos_estantes",
        "descartes_fds",
        "historicos_produtos",
    }
)
