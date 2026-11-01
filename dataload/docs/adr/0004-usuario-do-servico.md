# ADR 0004: Usar o usuário do serviço, sem usuário dedicado ao seed

Status: Aceita

## Contexto

O Aiven cria um usuário administrador por serviço (por exemplo `avnadmin`). Seria possível criar um usuário com privilégios reduzidos só para o seed.

## Decisão

Usar o usuário do serviço, sem criar um usuário só para o seed.

## Consequências

- A proteção do `main` contra apagar dados depende das travas do código, não de privilégios no banco (ver [ADR 0029](0029-travas-do-banco-principal.md)).
