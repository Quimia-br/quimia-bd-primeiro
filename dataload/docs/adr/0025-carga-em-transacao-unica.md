# ADR 0025: Carga em uma única transação

Status: Aceita

## Contexto

Uma carga que falha no meio deixaria o banco com dados parciais e inconsistentes.

## Decisão

- A carga toda roda em uma transação: cada tabela é inserida com um único `insert(Modelo.__table__)` com a lista de linhas e `RETURNING` das PKs (`sort_by_parameter_order=True` garante a ordem dos IDs).
- `admin_log_edicoes` é inserida por último: o `id_registro` aponta para `produtos`, `descartes_fds` e outras tabelas, mas não é FK, então a ordem calculada pelas FKs não enxerga essa dependência.
- `tipos_historicos` usa `ON CONFLICT (nome) DO NOTHING` e depois busca os IDs pelo nome, porque os tipos podem já existir.

## Consequências

- Se qualquer tabela falhar, nada fica gravado.
