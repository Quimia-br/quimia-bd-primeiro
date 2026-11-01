# ADR 0006: `database/sql/` é a fonte da verdade e não há Alembic

Status: Aceita

## Contexto

O schema do banco é mantido na pasta `database/`, separada da ferramenta de carga, a partir de `database/sql/01_ddl.sql` e `database/sql/02_fks.sql`. Esses scripts começam com `DROP TABLE ... CASCADE`.

## Decisão

- `database/sql/` é a fonte da verdade do schema, e o seed se adapta a ele.
- O seed nunca executa esses scripts.
- Não usar Alembic: o projeto não cria nem altera tabelas, então uma ferramenta de migração não teria função e acrescentaria baseline, `stamp` e credenciais extras.
- O seed não faz melhorias de schema. Sugestões de mudança ficam para o time decidir fora do projeto.

## Consequências

- Como aplicar mudanças de schema nos dois bancos é uma questão em aberto, fora do escopo do seed.
- Mudanças de schema seguem o fluxo descrito no [ADR 0008](0008-mudanca-de-schema-em-tres-lugares.md).
