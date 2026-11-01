# ADR 0022: IDs provisórios nos geradores

Status: Aceita

## Contexto

Os geradores produzem linhas que se referenciam por chave estrangeira, mas os IDs reais só existem depois do insert, criados pelo banco.

## Decisão

Cada linha recebe o ID provisório `posição + 1` da sua tabela, e as chaves estrangeiras usam esses IDs. A carga troca pelos IDs reais devolvidos pelo `RETURNING`.

## Consequências

- Os geradores funcionam sem banco, o que permite o `seed run --dry-run` e os testes unitários.
