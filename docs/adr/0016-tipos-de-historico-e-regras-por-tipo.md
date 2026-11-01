# ADR 0016: Tipos de histórico e regras por tipo em `data/reference`

Status: Aceita

## Contexto

Cada histórico tem um tipo, e cada tipo impõe regras sobre quantos produtos e se exige estante. Esses valores ainda são provisórios e podem mudar.

## Decisão

- Os tipos de histórico são criados pelo seed a partir de `data/reference`, com `ON CONFLICT (nome) DO NOTHING`, nos dois alvos. Valores provisórios: USO, MISTURA, DESCARTE, ARMAZENAMENTO e VERIFICACAO.
- Cômodos: COZINHA, LAVANDERIA, AREA_SERVICO, BANHEIRO, GARAGEM, DESPENSA, QUARTO e SALA.
- As regras por tipo ficam em YAML: USO, DESCARTE e ARMAZENAMENTO com exatamente 1 produto; VERIFICACAO com 0 a 3; MISTURA com 2 a 4. ARMAZENAMENTO e VERIFICACAO exigem estante.
- Um ARMAZENAMENTO exige o produto na estante (`produtos_estantes`) com `data_adicao` até a data do histórico.

## Consequências

- Alterar tipos, cômodos ou regras é editar os YAML, sem mexer em código.
