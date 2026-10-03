# 0002. Schema public, usuário quimia_seed e credenciais separadas para o Alembic

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

O usuário padrão do Aiven (`avnadmin`) pode tudo, inclusive apagar tabelas. O seed só precisa ler e inserir (e, no `test`, limpar as tabelas). As migrações do Alembic precisam criar e alterar tabelas.

## Decisão

- As tabelas ficam no schema `public` (`SEED_DB_SCHEMA=public`).
- O seed conecta como `quimia_seed`, criado separadamente em cada serviço:
  - **test:** `SELECT`, `INSERT`, `DELETE` e `TRUNCATE` em todas as tabelas do `public` (o `seed reset` precisa de `TRUNCATE`).
  - **main:** só `SELECT` e `INSERT`, sem `DELETE` nem `TRUNCATE`. É uma proteção no próprio banco, além das travas do código.
- O SQL de criação e dos `GRANT`s dos dois cenários fica em `sql/grants/`. O Nicolas executa como `avnadmin`, depois de cada `GRANT` ser explicado. O SQL cobre colunas identity e tabelas criadas por migrações futuras (`ALTER DEFAULT PRIVILEGES`).
- O Alembic conecta como `avnadmin`, com variáveis próprias: `SEED_MIGRATION_DB_USER` e `SEED_MIGRATION_DB_PASSWORD`. O `migrations/env.py` usa essas variáveis; o seed usa `SEED_DB_USER` e `SEED_DB_PASSWORD`.

## Alternativas descartadas

- **Seed como `avnadmin`:** um bug ou um alvo errado poderia apagar dados do principal.
- **Schema próprio (`quimia`):** o app e o DDL já usam `public`.
- **Mesmas permissões nos dois serviços:** perderia a proteção do banco contra `DELETE`/`TRUNCATE` no principal.

## Consequências

- No `main`, um `seed reset` falharia por falta de permissão, mesmo se as travas do código falhassem.
- Toda tabela nova criada por migração precisa receber os `GRANT`s (garantido pelos privilégios padrão).
- Os arquivos `.env.*` têm duas credenciais por alvo.
