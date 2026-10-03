# Documentação do data-load-quimia

| Arquivo | Conteúdo |
|---|---|
| [pauta-reuniao.md](pauta-reuniao.md) | Decisões pendentes para o time, prontas para levar à reunião. |
| [decisoes/](decisoes/) | Decisões já tomadas, uma por arquivo, no formato ADR. |
| [schema/observacoes-modelagem.md](schema/observacoes-modelagem.md) | Problemas e limitações do DDL atual. |
| [schema/consultas-verificacao.md](schema/consultas-verificacao.md) | Consultas SQL de verificação, com objetivo e interpretação. |
| [problemas-e-solucoes.md](problemas-e-solucoes.md) | Erros encontrados no projeto: sintoma, causa e solução. |

## Decisões (ADRs)

| Nº | Título |
|---|---|
| [0001](decisoes/0001-sem-docker-aiven-dois-servicos.md) | Sem Docker; `test` e `main` em serviços separados do Aiven, com SSL verify-full |
| [0002](decisoes/0002-schema-public-e-usuario-quimia-seed.md) | Schema `public`, usuário `quimia_seed` e credenciais separadas para o Alembic (substituída em parte pela 0014) |
| [0003](decisoes/0003-sql-como-fonte-da-verdade.md) | `sql/` como fonte da verdade, teste de paridade e baseline por `stamp` |
| [0004](decisoes/0004-cas-number-unique-mantido.md) | `cas_number UNIQUE` mantido por enquanto |
| [0005](decisoes/0005-nenhuma-melhoria-de-schema-agora.md) | Nenhuma melhoria de schema agora |
| [0006](decisoes/0006-idade-minima-e-data-nascimento.md) | Idade mínima de 18 anos e 10% com `data_nascimento` nula |
| [0007](decisoes/0007-regras-por-tipo-de-historico.md) | Regras de produtos e estante por tipo de histórico |
| [0008](decisoes/0008-admin-log-somente-no-test.md) | `admin_log_edicoes` só no `test`, com regras por ação |
| [0009](decisoes/0009-pool-e-volume-dos-perfis.md) | Pool 2 + overflow 1 e perfil `perf` com ~50 mil linhas |
| [0010](decisoes/0010-fuso-horario-das-colunas-timestamp.md) | Fuso horário das colunas TIMESTAMP sem fuso |
| [0011](decisoes/0011-tipos-de-historico-por-migracao.md) | Tipos de histórico inseridos por migração |
| [0012](decisoes/0012-valores-de-comodo-e-tipos-de-historico.md) | Valores provisórios de cômodo e tipos de histórico |
| [0013](decisoes/0013-main-sem-dados-sinteticos.md) | O `main` recebe só referência e catálogo revisado (substituída pela 0015) |
| [0014](decisoes/0014-seed-usa-o-usuario-do-servico.md) | O seed usa o usuário do serviço, sem criar `quimia_seed` |
| [0015](decisoes/0015-main-recebe-dados-ficticios.md) | O `main` recebe dados fictícios, exceto auditoria, com `--allow-synthetic` |
| [0016](decisoes/0016-env-e-o-arquivo-do-principal.md) | O `.env` é o arquivo do banco principal, com proteções contra injeção automática |
| [0017](decisoes/0017-ssl-verify-ca.md) | SSL `verify-ca` em vez de `verify-full`, por limitação do libpq no Windows |

## Regra de documentação

Sempre que surgir um problema de consulta, de modelagem, de dados ou de ambiente, ou uma decisão for tomada, o registro vai para o arquivo certo **no mesmo commit da mudança**:

- decisão tomada → novo ADR em `decisoes/` (próximo número livre) e linha na tabela acima;
- decisão que depende do time → item em `pauta-reuniao.md`;
- limitação do DDL → `schema/observacoes-modelagem.md`;
- consulta SQL útil → `schema/consultas-verificacao.md`;
- erro e sua solução → `problemas-e-solucoes.md`.
