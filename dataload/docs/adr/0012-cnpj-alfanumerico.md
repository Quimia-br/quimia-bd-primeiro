# ADR 0012: CNPJ alfanumérico

Status: Aceita

## Contexto

O formato alfanumérico do CNPJ da Receita Federal está em vigor desde 31/07/2026.

## Decisão

Validar o CNPJ com 12 caracteres `[0-9A-Z]` e 2 dígitos verificadores numéricos, calculados por módulo 11, com cada caractere valendo o código ASCII menos 48.

## Consequências

- Os CNPJs numéricos continuam válidos.
- Testado com o exemplo oficial `12.ABC.345/01DE-35`.
