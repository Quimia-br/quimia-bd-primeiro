# 0006. Idade mínima de 18 anos e 10% com data_nascimento nula

- **Status:** aceita (idade oficial pendente; ver [pauta, item 10](../pauta-reuniao.md))
- **Data:** 2026-10-03

## Contexto

O app lida com produtos químicos e pretende exigir idade mínima. O DDL permite `usuarios.data_nascimento` nula.

## Decisão

- Idade mínima de **18 anos**, calculada **na data de cadastro** do usuário, e não na data de hoje: quem se cadastrou em 2024 precisava ter 18 anos em 2024.
- **10%** dos usuários sintéticos ficam com `data_nascimento` nula.
- Os dois valores ficam no perfil (`config/`). Se o time definir outra idade, basta mudar o perfil, sem alterar o código.
- O cálculo é feito sobre datas com fuso, antes da conversão para gravação ([ADR 0010](0010-fuso-horario-das-colunas-timestamp.md)).

## Alternativas descartadas

- **Idade calculada na data de hoje:** usuários antigos que eram menores no cadastro passariam na verificação.
- **13 ou 16 anos:** produtos químicos sugerem público adulto.
- **Nenhuma data nula:** não representaria o que o banco aceita hoje.

## Consequências

- Os testes verificam a idade mínima na data de cadastro e a fração de nulos.
