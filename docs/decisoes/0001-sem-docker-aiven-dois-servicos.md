# 0001. Sem Docker; bancos test e main em serviços separados do Aiven, com SSL verify-full

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

O projeto precisa de um banco para desenvolvimento e testes e de outro para a carga real. A máquina de desenvolvimento é Windows e o projeto não terá Docker. O banco da Quimia já roda no Aiven (PostgreSQL gerenciado).

## Decisão

- Dois serviços distintos no Aiven: `test` (desenvolvimento, testes de integração, perfis grandes) e `main` (banco principal).
- O alvo padrão de todos os comandos é `test`.
- Conexão sempre com SSL `sslmode=verify-full` e `sslrootcert` apontando para o CA de cada serviço em `certs/` (fora do Git).
- Credenciais em `.env.test` e `.env.main` (fora do Git), com `.env.example` versionado contendo só nomes e valores fictícios.
- Sem Docker nem Testcontainers. Os testes de integração usam schemas temporários no serviço `test`.

## Alternativas descartadas

- **Postgres local em Docker/Testcontainers:** o projeto não terá Docker.
- **Um único serviço com dois databases:** um erro de configuração afetaria o banco principal; serviços separados isolam credenciais, limites e backups.
- **`sslmode=require`:** criptografa, mas não verifica o certificado do servidor, o que permite ataque de intermediário.

## Consequências

- Os testes de integração dependem de rede e de liberar o IP na allowlist do Aiven.
- Os testes unitários e o CI rodam sem banco.
- Cada viagem ao banco é remota, então os inserts são sempre em lote.
