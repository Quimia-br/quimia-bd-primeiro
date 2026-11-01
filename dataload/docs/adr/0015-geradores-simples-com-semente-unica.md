# ADR 0015: Geradores simples com Faker e uma semente única

Status: Aceita

## Contexto

É preciso gerar dados sintéticos em pt_BR que sejam reproduzíveis entre execuções. Para 100 linhas por tabela, uma biblioteca de fábricas como a Polyfactory não traria vantagem.

## Decisão

- Os geradores são funções simples com Faker `pt_BR` e `random.Random`, com uma semente única (`--seed`, padrão 42).
- Sem Polyfactory.
- A mesma semente e o mesmo momento de carga geram exatamente os mesmos dados (as datas são relativas ao momento da carga).
- O `senha_hash` usa um salt derivado da semente, para também ser reproduzível.

## Consequências

- A senha é a mesma em todas as contas sintéticas, então o salt determinístico não expõe nada.
