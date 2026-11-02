# ADR 0009: `cas_number` não é UNIQUE no banco

Status: Aceita

## Contexto

O número CAS identifica uma substância química, e várias marcas podem vender produtos com a mesma substância. A restrição UNIQUE em `cas_number` impedia isso.

## Decisão

Remover o UNIQUE de `cas_number` do DDL e do modelo.

## Consequências

- O catálogo continua com 100 substâncias distintas e o seed gera um produto por entrada.
