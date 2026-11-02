# database

Schema PostgreSQL do **Quimia** e a documentação da modelagem. Esta pasta não tem código Python: a ferramenta que popula o banco está em [`../dataload/`](../dataload/README.md) (carga `seed`).

> [!CAUTION]
> Os scripts de `sql/` começam com `DROP TABLE ... CASCADE`. **Nunca os execute no Aiven** sobre um banco com dados.

## Conteúdo

| Caminho | O que é |
|---|---|
| [`sql/01_ddl.sql`](sql/01_ddl.sql) | Tabelas, CHECKs e UNIQUEs. **Fonte da verdade do schema.** |
| [`sql/02_fks.sql`](sql/02_fks.sql) | Chaves estrangeiras |
| [`sql/03_views.sql`](sql/03_views.sql) | Views do dashboard |
| [`docs/nomenclatura/`](docs/nomenclatura/naming-conversation.md) | Convenção de nomenclatura e padronização de normas SQL (também em `.docx` e `.pdf`) |
| [`legacy/`](legacy) | Seeds JSON e `requirements.txt` da versão antiga, mantidos só para consulta |

Ordem de execução em um banco novo e vazio: `01_ddl.sql`, `02_fks.sql` e `03_views.sql`.

## Mudou o schema?

Atualize os scripts de `sql/` e, na ferramenta de carga, `dataload/src/seed/modelos.py` e `dataload/src/seed/contratos.py`, no mesmo commit. O `uv run pytest` confere modelos e contratos contra o `01_ddl.sql`.

O histórico da antiga branch `database` foi incorporado a este repositório e continua visível no `git log`.
