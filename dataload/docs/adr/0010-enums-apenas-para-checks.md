# ADR 0010: Enums só para os CHECKs do DDL

Status: Aceita

## Contexto

Algumas colunas têm CHECK no banco (`status`, `porte`, `acao`). Outras, como `comodo` e o nome dos tipos de histórico, não têm, e seus valores podem mudar com o tempo.

## Decisão

Usar enums em Python só para os CHECKs do DDL. Um teste confere os valores contra `database/sql/01_ddl.sql`. Os valores de `comodo` e dos tipos de histórico ficam em `data/reference`.

## Consequências

- Esses valores mudam sem alterar código.
