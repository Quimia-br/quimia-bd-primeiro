# 0004. cas_number UNIQUE mantido por enquanto

- **Status:** aceita (provisória; ver [pauta, item 1](../pauta-reuniao.md))
- **Data:** 2026-10-03

## Contexto

`produtos.cas_number` é `UNIQUE`. O CAS identifica a substância, não o produto comercial, então duas marcas da mesma substância não podem coexistir. Não foi intencional, mas o time ainda não decidiu a alternativa.

## Decisão

- O DDL fica como está e nenhuma migração é criada agora.
- O seed respeita o `UNIQUE` atual: um produto por CAS, com o número de produtos limitado ao número de CAS distintos do catálogo.
- O gerador de produtos é parametrizado: a chave natural e o limite de volume vêm de um único ponto de configuração. Se o `UNIQUE` mudar, basta ajustar esse ponto, sem reescrever o pipeline.
- A decisão definitiva vai para a pauta, com três alternativas: `UNIQUE (cas_number, marca)`; `UNIQUE (id_usuario_empresa, nome)`; tabelas `substancias` e `produtos_substancias`.

## Alternativas descartadas

- **Mudar o schema agora:** depende de decisão do time e afeta o backend.
- **Gerar CAS falsos para ter mais produtos:** violaria a regra de não inventar dados químicos.

## Consequências

- Os perfis grandes têm muitos usuários, mas poucos produtos (no máximo o tamanho do catálogo).
- No `main`, o `cas_number` é a chave natural de `produtos` no `ON CONFLICT DO NOTHING`.
