# ADR 0017: Idade mínima de 18 anos

Status: Aceita

## Contexto

Os usuários do app devem ser maiores de idade, e `data_nascimento` é opcional no schema.

## Decisão

A idade mínima de 18 anos é calculada na data de cadastro, e 10% dos usuários ficam sem `data_nascimento`. Os dois valores ficam em `config.py`.

## Consequências

- O `seed verificar` confere a idade mínima no banco.
