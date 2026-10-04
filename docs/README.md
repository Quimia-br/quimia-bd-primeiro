# Documentação do data-load-quimia

| Arquivo | Conteúdo |
|---|---|
| [../README.md](../README.md#decisões) | Visão geral, instalação, comandos e a seção **Decisões** (decisões já tomadas e o motivo). |
| [pauta-reuniao.md](pauta-reuniao.md) | Decisões pendentes para o time, prontas para levar à reunião, incluindo as limitações do schema. |
| [problemas-e-solucoes.md](problemas-e-solucoes.md) | Erros encontrados no projeto: sintoma, causa e solução. |

## Regra de documentação

Sempre que surgir um problema de consulta, de modelagem, de dados ou de ambiente, ou uma decisão for tomada, o registro vai para o arquivo certo **no mesmo commit da mudança**:

- decisão tomada → seção **Decisões** do `README.md`;
- decisão que depende do time, ou limitação do schema → item em `pauta-reuniao.md`;
- erro e sua solução → `problemas-e-solucoes.md`.
