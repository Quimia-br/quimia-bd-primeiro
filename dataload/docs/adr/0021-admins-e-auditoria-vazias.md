# ADR 0021: `admins` e `admin_log_edicoes` ficam vazias

Status: Aceita

## Contexto

`admin_log_edicoes.id_admin` é NOT NULL e referencia `admins`. Auditoria falsa no banco principal é pior do que auditoria vazia.

## Decisão

Os administradores não são gerados pelo seed, em qualquer alvo (`QUANTIDADES` em `config.py` com 0). Sem admins também não há log de auditoria.

## Consequências

- Os geradores continuam no código: basta aumentar as quantidades para voltar a gerar as tabelas.
- Mesmo assim, o log de auditoria continua barrado no `main`.
