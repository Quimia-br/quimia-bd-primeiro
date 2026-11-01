# ADR 0014: 100 registros por tabela

Status: Aceita

## Contexto

O seed precisa de volume suficiente para exercitar o app e as regras de negócio, sem pesar no banco.

## Decisão

Gerar 100 registros por tabela, valor fixo em `config.py` (fácil de mudar). Exceções:

- `tipos_historicos` recebe só os tipos de `data/reference` (cinco);
- `admins` e `admin_log_edicoes` ficam vazias ([ADR 0021](0021-admins-e-auditoria-vazias.md));
- `localizacoes` tem uma por usuário, e `descartes_fds` um por produto.

## Consequências

- Mudar o volume é editar `QUANTIDADES` em `config.py`.
