# ADR 0001: Dois serviços separados no Aiven, sem Docker

Status: Aceita

## Contexto

O seed grava no PostgreSQL da Quimia, hospedado no Aiven. É preciso um banco onde testar à vontade e outro, o principal, que precisa ser protegido.

## Decisão

Não usar Docker. Usar dois serviços separados no Aiven: `test`, que é o alvo padrão de todos os comandos, e `main`, o banco principal, escolhido só com `--target main`.

## Consequências

- Serviços separados isolam credenciais, limites e backups.
- Qualquer comando sem `--target` age apenas no `test`.
