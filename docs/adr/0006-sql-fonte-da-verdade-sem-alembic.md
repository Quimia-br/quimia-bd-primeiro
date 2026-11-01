# ADR 0006: `sql/` é a fonte da verdade e não há Alembic

Status: Aceita

## Contexto

O schema do banco é criado e alterado fora deste projeto, a partir de `sql/01_ddl.sql` e `sql/02_fks.sql`. Esses scripts começam com `DROP TABLE ... CASCADE`.

## Decisão

- `sql/` é a fonte da verdade do schema, e o seed se adapta a ele.
- O seed nunca executa esses scripts.
- Não usar Alembic: o projeto não cria nem altera tabelas, então uma ferramenta de migração não teria função e acrescentaria baseline, `stamp` e credenciais extras.
- O seed não faz melhorias de schema. Sugestões de mudança ficam para o time decidir fora do projeto.

## Consequências

- Como aplicar mudanças de schema nos dois bancos é uma questão em aberto, fora do escopo do seed.
- Mudanças de schema seguem o fluxo descrito no [ADR 0008](0008-mudanca-de-schema-em-tres-lugares.md).
