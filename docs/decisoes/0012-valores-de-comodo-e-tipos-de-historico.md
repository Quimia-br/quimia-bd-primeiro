# 0012. Valores provisórios de cômodo e tipos de histórico

- **Status:** aceita (provisória; ver [pauta, item 11](../pauta-reuniao.md))
- **Data:** 2026-10-03

## Contexto

`estantes.comodo` não tem CHECK (o default é `'DESCONHECIDO'`), e `tipos_historicos` não tem lista oficial.

## Decisão

- Cômodos: `COZINHA`, `LAVANDERIA`, `AREA_SERVICO`, `BANHEIRO`, `GARAGEM`, `DESPENSA`, `QUARTO`, `SALA`. O seed não gera `DESCONHECIDO`, que é só o default do banco.
- Tipos de histórico: `USO`, `MISTURA`, `DESCARTE`, `ARMAZENAMENTO`, `VERIFICACAO`.
- As listas ficam em `data/reference/` e no domínio como `StrEnum`.

## Alternativas descartadas

- **Valores em minúsculas:** os CHECKs do DDL (status, porte, ação) usam maiúsculas; o mesmo padrão é mantido.

## Consequências

- Se o time definir outros valores, basta editar o YAML (e a migração dos tipos).
