# ADR 0029: Travas de proteção do banco principal

Status: Aceita

## Contexto

O seed usa o usuário do serviço ([ADR 0004](0004-usuario-do-servico.md)), então o banco não impede, por privilégios, que dados do `main` sejam apagados.

## Decisão

- `reset` é bloqueado no `main` pelo código.
- Comandos contra o `main` são sempre executados manualmente por uma pessoa, nunca por assistentes ou automações.
- `SEED_PASSWORD_PLAIN` (senha dos usuários fictícios) deve ser diferente em cada arquivo de configuração.

## Consequências

- A proteção do `main` depende destas travas no código e do processo de uso.
