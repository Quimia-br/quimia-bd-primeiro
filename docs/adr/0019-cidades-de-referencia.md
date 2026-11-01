# ADR 0019: Cidades de referência com faixa de CEP e coordenadas

Status: Aceita

## Contexto

CEP, cidade e coordenadas de uma localização precisam ser coerentes entre si.

## Decisão

Manter em `data/reference/cidades.yaml` 14 cidades, cada uma com faixa de CEP e coordenadas do centro, para que o CEP gerado combine com a cidade.

## Consequências

- As faixas e coordenadas são aproximadas e devem ser conferidas antes de uso fora do banco de teste.
