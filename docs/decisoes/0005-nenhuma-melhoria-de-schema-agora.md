# 0005. Nenhuma melhoria de schema agora

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

A análise do DDL encontrou várias melhorias possíveis (índice em `lower(email)`, CHECK de CEP, índices nas FKs, TIMESTAMPTZ, JSONB, entre outras). Todas afetam o backend ou os dados existentes, e o schema é compartilhado com o time do app.

## Decisão

- Nenhuma melhoria é aplicada agora. Nenhuma migração é criada e os scripts `sql/` não são alterados.
- Todas as melhorias vão para [`docs/pauta-reuniao.md`](../pauta-reuniao.md), escritas para quem não acompanhou o projeto, com situação atual, problema, opções, impacto, consulta de verificação, recomendação e decisão em branco.
- O seed compensa no código o que o banco não garante (por exemplo, e-mails em minúsculas e CEP com 8 dígitos).

## Alternativas descartadas

- **Aplicar já as melhorias de baixo risco (como índices):** mesmo as simples precisam ser combinadas com o time, para o DDL do app continuar sendo a referência.

## Consequências

- O seed tem validações que, no futuro, podem passar para o banco.
- Cada melhoria aprovada vira uma migração, com a atualização de `sql/` e o teste de paridade.
