# 0007. Regras de produtos e estante por tipo de histórico

- **Status:** aceita (lista oficial pendente; ver [pauta, item 11](../pauta-reuniao.md))
- **Data:** 2026-10-03

## Contexto

Um histórico registra uma ação do usuário (uso, mistura, descarte etc.), pode estar ligado a uma estante e pode ter produtos em `historicos_produtos`. O DDL não define quantos produtos cada tipo tem nem se a estante é obrigatória.

## Decisão

As regras ficam em YAML em `data/reference/`, junto da lista de tipos, para mudar sem alterar código:

| Tipo | Produtos | Estante |
|---|---|---|
| USO | exatamente 1 | opcional |
| DESCARTE | exatamente 1 | opcional |
| ARMAZENAMENTO | exatamente 1 | obrigatória |
| VERIFICACAO | 0 a 3 | obrigatória |
| MISTURA | 2 a 4 | opcional |

Coerência com `produtos_estantes`:

- Um ARMAZENAMENTO do produto X na estante Y no momento D exige a linha (Y, X) em `produtos_estantes`, com `data_adicao` igual a D ou anterior.
- Numa VERIFICACAO com produtos, os produtos precisam estar na estante verificada.

As regras são verificadas nos testes em memória e nas consultas SQL de integração.

## Alternativas descartadas

- **Regras fixas no código:** cada mudança do time exigiria alterar e publicar código.
- **0 ou 1 produto para todos os tipos que não são MISTURA:** não representa ARMAZENAMENTO e VERIFICACAO.

## Consequências

- O gerador de históricos depende das estantes e de `produtos_estantes` já gerados.
- Se o time mudar a lista, basta editar o YAML (e criar a migração dos tipos, [ADR 0011](0011-tipos-de-historico-por-migracao.md)).
