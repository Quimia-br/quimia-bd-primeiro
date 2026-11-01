# ADR 0028: Carga sintética restrita no banco principal

Status: Aceita

## Contexto

O `main` é o banco principal, e dados fictícios nele precisam ser uma escolha explícita. Os produtos do catálogo precisam de uma empresa dona (`id_usuario_empresa` é NOT NULL), e as empresas são sintéticas.

## Decisão

- O `main` pode receber dados fictícios (exceto auditoria), só com `--allow-synthetic`, uma confirmação extra e o nome do banco digitado.
- Sem a opção, o `main` recebe só os tipos de histórico.
- Com a opção, os produtos do `main` vêm só das entradas revisadas do catálogo ([ADR 0018](0018-catalogo-de-produtos-escrito-a-mao.md)).

## Consequências

- Enquanto nenhuma entrada do catálogo estiver revisada, a carga sintética no `main` é recusada.
