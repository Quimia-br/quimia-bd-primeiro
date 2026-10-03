# 0014. O seed usa o usuário do serviço, sem criar quimia_seed

- **Status:** aceita (substitui em parte a [ADR 0002](0002-schema-public-e-usuario-quimia-seed.md))
- **Data:** 2026-10-03

## Contexto

A ADR 0002 previa um usuário `quimia_seed` com privilégios mínimos em cada serviço (no `main`, só `SELECT` e `INSERT`), para o próprio banco recusar `DELETE` e `TRUNCATE` do seed, além das travas do código. Antes de criar o usuário, o Nicolas decidiu não criá-lo.

## Decisão

- O usuário `quimia_seed` **não será criado**. O seed conecta com o usuário configurado em `SEED_DB_USER` e `SEED_DB_PASSWORD` de cada `.env`, que é o usuário do serviço no Aiven (por exemplo, `avnadmin`).
- O schema continua sendo o `public`.
- `SEED_MIGRATION_DB_USER` e `SEED_MIGRATION_DB_PASSWORD` passam a ser **opcionais**. Sem elas, o Alembic usa a mesma credencial do seed. Elas continuam disponíveis, caso um dia as migrações usem outro usuário.
- Como o usuário é dono das tabelas, o `seed reset` (só no `test`) pode usar `TRUNCATE ... RESTART IDENTITY CASCADE` diretamente.

## Alternativas descartadas

- **Usuário `quimia_seed` com privilégios mínimos:** dava uma segunda camada de proteção no `main`, mas exigia criar e manter um usuário e as suas permissões em cada serviço.

## Consequências

- **A proteção do `main` contra apagar dados depende só do código:** as travas da CLI (Fase 8), que bloqueiam `reset`, `perf` e carga sintética no `main`, e os testes que provam esses bloqueios. O banco não recusa um `DELETE` ou `TRUNCATE` vindo do seed.
- A regra de que o assistente nunca executa nada contra o `main` continua valendo.
- O `seed check` mostra o usuário conectado, para conferir qual credencial está em uso.
