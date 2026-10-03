# 0011. Tipos de histórico inseridos por migração

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

A tabela `tipos_historicos` é uma tabela de referência: o app depende dela para funcionar.

## Decisão

- Os tipos entram no banco por uma migração do Alembic com `op.bulk_insert`, separada da baseline.
- O seed não insere tipos; apenas lê os IDs existentes e valida que a lista do banco bate com `data/reference/`.

## Alternativas descartadas

- **Inserir pelo seed:** um banco migrado mas sem seed ficaria sem tipos, e o app quebraria.

## Consequências

- Mudar a lista exige uma nova migração e a edição do YAML.
