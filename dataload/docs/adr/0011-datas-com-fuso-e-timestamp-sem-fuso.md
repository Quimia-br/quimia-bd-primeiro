# ADR 0011: Datas com fuso nos contratos e colunas `TIMESTAMP` sem fuso

Status: Aceita

## Contexto

As colunas de data do banco são `TIMESTAMP` sem fuso horário, o que deixa ambíguo em que fuso cada data foi gravada.

## Decisão

- Os contratos recusam datas sem fuso ou no futuro.
- As datas são geradas com fuso em `America/Sao_Paulo`, convertidas para `SEED_TIMEZONE` (padrão UTC) e gravadas sem fuso. A conversão acontece só na carga.

## Consequências

- O `seed check` avisa se o fuso do servidor for diferente de `SEED_TIMEZONE`, e o `seed run` se recusa a rodar nesse caso (a menos que se use `--ignorar-fuso`).
