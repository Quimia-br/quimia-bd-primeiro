# Decisões de arquitetura (ADRs)

Este diretório registra as decisões técnicas do projeto **data-load-quimia**, uma por arquivo, no formato simples de ADR (*Architecture Decision Record*):

- **Contexto:** o problema ou a restrição que levou à decisão.
- **Decisão:** o que foi escolhido.
- **Consequências:** o que passa a valer por causa da escolha, incluindo riscos e limitações.

Os arquivos são numerados na ordem em que aparecem aqui (`0001-...`, `0002-...`). Uma decisão que mudar deve ganhar um novo ADR que substitui o anterior, em vez de reescrever o histórico. Para visão geral, instalação e comandos, veja o [README do projeto](../../../README.md).

## Ambiente e conexão

| ADR | Decisão |
|---|---|
| [0001](0001-dois-servicos-no-aiven-sem-docker.md) | Dois serviços separados no Aiven, sem Docker |
| [0002](0002-arquivos-env-por-alvo.md) | Um arquivo de configuração por alvo |
| [0003](0003-ssl-verify-ca.md) | SSL `verify-ca` em vez de `verify-full` |
| [0004](0004-usuario-do-servico.md) | Usar o usuário do serviço, sem usuário dedicado ao seed |
| [0005](0005-pool-pequeno-e-schema-public.md) | Pool de conexões pequeno e schema `public` |

## Schema

| ADR | Decisão |
|---|---|
| [0006](0006-sql-fonte-da-verdade-sem-alembic.md) | `database/sql/` é a fonte da verdade e não há Alembic |
| [0007](0007-modelos-orm-e-contratos-pydantic.md) | Modelos ORM só para descrever tabelas e contratos Pydantic para validar linhas |
| [0008](0008-mudanca-de-schema-em-tres-lugares.md) | Mudança de schema atualiza três lugares juntos |
| [0009](0009-cas-number-sem-unique.md) | `cas_number` não é UNIQUE no banco |
| [0010](0010-enums-apenas-para-checks.md) | Enums só para os CHECKs do DDL |
| [0011](0011-datas-com-fuso-e-timestamp-sem-fuso.md) | Datas com fuso nos contratos e colunas `TIMESTAMP` sem fuso |
| [0012](0012-cnpj-alfanumerico.md) | CNPJ alfanumérico |
| [0013](0013-emails-sinteticos-em-dominios-reservados.md) | E-mails sintéticos só em domínios reservados |

## Dados

| ADR | Decisão |
|---|---|
| [0014](0014-cem-registros-por-tabela.md) | 100 registros por tabela |
| [0015](0015-geradores-simples-com-semente-unica.md) | Geradores simples com Faker e uma semente única |
| [0016](0016-tipos-de-historico-e-regras-por-tipo.md) | Tipos de histórico e regras por tipo em `data/reference` |
| [0017](0017-idade-minima-de-18-anos.md) | Idade mínima de 18 anos |
| [0018](0018-catalogo-de-produtos-escrito-a-mao.md) | Catálogo de produtos escrito à mão e revisado antes de ir ao `main` |
| [0019](0019-cidades-de-referencia.md) | Cidades de referência com faixa de CEP e coordenadas |
| [0020](0020-fotos-por-links-externos.md) | Fotos por links externos |
| [0021](0021-admins-e-auditoria-vazias.md) | `admins` e `admin_log_edicoes` ficam vazias |

## Geradores

| ADR | Decisão |
|---|---|
| [0022](0022-ids-provisorios-nos-geradores.md) | IDs provisórios nos geradores |
| [0023](0023-distribuicao-de-produtos-estantes-e-historicos.md) | Como produtos, estantes e históricos são distribuídos |
| [0024](0024-descricoes-neutras-nos-historicos.md) | Descrições neutras nos históricos |

## Carga

| ADR | Decisão |
|---|---|
| [0025](0025-carga-em-transacao-unica.md) | Carga em uma única transação |
| [0026](0026-recusas-antes-de-gravar.md) | Recusas antes de gravar |
| [0027](0027-verificacao-de-regras-no-banco.md) | `seed verificar` confere as regras de negócio no banco |

## Banco principal

| ADR | Decisão |
|---|---|
| [0028](0028-carga-sintetica-restrita-no-banco-principal.md) | Carga sintética restrita no banco principal |
| [0029](0029-travas-do-banco-principal.md) | Travas de proteção do banco principal |
