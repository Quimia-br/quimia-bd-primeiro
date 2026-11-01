# ADR 0008: Mudança de schema atualiza três lugares juntos

Status: Aceita

## Contexto

O schema existe em `sql/` (fonte da verdade), em `modelos.py` (ORM) e em `contratos.py` (validação).

## Decisão

Toda mudança de schema atualiza `sql/`, `modelos.py` e `contratos.py` juntos.

## Consequências

- O `seed check` mostra divergências entre os modelos e o banco, e o `seed run` se recusa a rodar se houver alguma.
- Um teste unitário confere modelos × DDL e contratos × modelos.
