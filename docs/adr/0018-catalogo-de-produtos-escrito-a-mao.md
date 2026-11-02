# ADR 0018: Catálogo de produtos escrito à mão e revisado antes de ir ao `main`

Status: Aceita

## Contexto

Produtos químicos trazem informação de segurança (descarte, dosagem, precauções). Inventar ou gerar esse conteúdo automaticamente seria perigoso.

## Decisão

O catálogo fica em `data/catalog/produtos.json`, escrito à mão:

- 100 substâncias distintas usadas em produtos de limpeza (alvejantes, desinfetantes, ácidos, álcalis, tensoativos, solventes, sequestrantes, espessantes, conservantes e fragrâncias), com CAS reais validados pelo dígito verificador.
- O nome do produto é genérico (`categoria (substância)`) e as marcas são claramente fictícias (`Marca Exemplo Alfa`...).
- Toda entrada começa com `"revisado": false`, `"fonte": "pendente de conferência"` e `data_consulta` nula.
- **Instrução de uso, dosagem técnica e os quatro campos de descarte ficam "pendente de revisão"**: são informação de segurança e nunca são inventados.
- Uma entrada só pode ser marcada como revisada com fonte, data de consulta e nenhum campo pendente.

## Consequências

- Só entradas revisadas vão para o `main` ([ADR 0028](0028-carga-sintetica-restrita-no-banco-principal.md)).
- Estado atual: as 100 entradas estão marcadas como revisadas, com CAS conferidos no PubChem, mas o catálogo continua sendo de **teste**. `instrucao_de_uso`, `dosagem_tecnica` e os textos de descarte são genéricos e não foram conferidos em FDS/FISPQ. Antes de uso real, cada entrada precisa dessa conferência.
