# 0003. sql/ como fonte da verdade, teste de paridade e baseline por stamp

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

O schema da Quimia já existe nos scripts `sql/01_ddl.sql` (tabelas) e `sql/02_fks.sql` (chaves estrangeiras), e já foi aplicado nos dois bancos do Aiven. O `01_ddl.sql` começa com `DROP TABLE ... CASCADE`.

## Decisão

- `sql/01_ddl.sql` e `sql/02_fks.sql` são a fonte da verdade. O seed se adapta ao schema, e não o contrário. Os arquivos ficam exatamente como foram entregues (os hooks de espaço em branco do pre-commit os ignoram).
- Os modelos SQLAlchemy espelham o DDL: nomes, tipos, tamanhos, nulidade, defaults, UNIQUEs, CHECKs, identity `ALWAYS` e nomes das FKs.
- Um **teste de paridade** aplica os scripts num schema temporário do `test`, cria outro a partir dos modelos e compara os dois por reflexão.
- **Os scripts nunca são executados no Aiven** fora desses schemas temporários de teste.
- A primeira migração do Alembic (baseline) representa o DDL. Como os dois bancos já têm o schema, eles recebem `alembic stamp <baseline>` em vez de `upgrade`. No `main`, o Nicolas executa o comando.
- Mudanças futuras viram migrações, com a atualização dos scripts `sql/` no mesmo commit.

## Alternativas descartadas

- **Gerar o schema a partir dos modelos:** o DDL do app é a referência do time.
- **Rodar a baseline nos bancos existentes:** falharia (as tabelas já existem) ou, pior, recriaria tudo.
- **Executar o DDL no `test` para "zerar":** apagaria qualquer dado sem controle; o `seed reset` faz isso de forma segura.

## Consequências

- Divergências entre DDL e modelos são detectadas automaticamente.
- Toda mudança de schema exige editar três lugares (migração, modelos e `sql/`), protegidos pelo teste de paridade.
