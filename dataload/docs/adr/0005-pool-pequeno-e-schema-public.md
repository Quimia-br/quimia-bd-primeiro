# ADR 0005: Pool de conexões pequeno e schema `public`

Status: Aceita

## Contexto

Os planos do Aiven têm limite de conexões simultâneas.

## Decisão

Usar um pool pequeno (2 conexões, mais 1 de excedente) e o schema `public`.

## Consequências

- O `seed check` mostra versão do servidor, conexões abertas, `max_connections` e tamanho do banco, para acompanhar o consumo.
