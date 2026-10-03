# Consultas de verificação

Consultas SQL somente leitura para diagnosticar o ambiente e conferir a coerência dos dados. **Nenhuma delas foi executada.** Rodar no `test` exige autorização no chat; no `main`, só o Nicolas executa.

As consultas que verificam se os dados atuais violariam uma mudança de schema ficam junto de cada item da [pauta](../pauta-reuniao.md), para o time ler tudo no mesmo lugar.

---

## Ambiente

### A1. Versão, fuso e limites do servidor

- **Objetivo:** saber a versão do Postgres, o fuso da sessão e o limite de conexões.
- **Consulta:**

  ```sql
  SELECT version()                          AS versao,
         current_setting('TimeZone')        AS fuso_sessao,
         current_setting('max_connections') AS max_conexoes;
  ```

- **Como interpretar:** `fuso_sessao` deve ser igual a `SEED_TIMEZONE` ([ADR 0010](../decisoes/0010-fuso-horario-das-colunas-timestamp.md)). `max_conexoes` orienta o tamanho do pool ([ADR 0009](../decisoes/0009-pool-e-volume-dos-perfis.md)).

### A2. Conexões abertas

- **Objetivo:** ver quantas conexões estão em uso e de quais aplicações.
- **Consulta:**

  ```sql
  SELECT application_name, usename, state, count(*) AS conexoes
  FROM pg_stat_activity
  WHERE datname = current_database()
  GROUP BY application_name, usename, state
  ORDER BY conexoes DESC;
  ```

- **Como interpretar:** o seed aparece como `quimia-seed`. Se o total estiver perto de `max_connections`, o seed pode falhar ao abrir o pool.

### A3. Tamanho do banco e das tabelas

- **Objetivo:** avaliar o espaço usado antes de um perfil grande.
- **Consulta:**

  ```sql
  SELECT pg_size_pretty(pg_database_size(current_database())) AS banco;

  SELECT relname AS tabela,
         pg_size_pretty(pg_total_relation_size(relid)) AS tamanho_total,
         n_live_tup AS linhas_estimadas
  FROM pg_stat_user_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(relid) DESC;
  ```

- **Como interpretar:** compare com o limite de armazenamento do plano no Aiven.

### A4. Revisão do Alembic

- **Objetivo:** saber em que migração o banco está.
- **Consulta:**

  ```sql
  SELECT version_num FROM alembic_version;
  ```

- **Como interpretar:** deve ser igual ao `head` do repositório (`uv run alembic heads`). Se a tabela não existir, o banco ainda não recebeu o `stamp` da baseline.

### A5. Privilégios do usuário do seed

- **Objetivo:** conferir que `quimia_seed` tem só o que precisa ([ADR 0002](../decisoes/0002-schema-public-e-usuario-quimia-seed.md)).
- **Consulta:**

  ```sql
  SELECT table_name, string_agg(privilege_type, ', ' ORDER BY privilege_type) AS privilegios
  FROM information_schema.role_table_grants
  WHERE grantee = 'quimia_seed' AND table_schema = 'public'
  GROUP BY table_name
  ORDER BY table_name;
  ```

- **Como interpretar:** no `test`, cada tabela mostra `DELETE, INSERT, SELECT, TRUNCATE`; no `main`, só `INSERT, SELECT`.

---

## Regras de negócio

As consultas abaixo devem retornar **zero linhas**. As demais regras entram aqui na fase de testes de integração.

### R1. Histórico com estante de outro usuário

- **Objetivo:** `historicos.id_estante`, quando preenchido, pertence ao usuário do histórico. O banco já garante pela FK composta; a consulta confirma.
- **Consulta:**

  ```sql
  SELECT h.id_historico, h.id_usuario, e.id_usuario AS dono_estante
  FROM historicos AS h
  JOIN estantes AS e ON e.id_estante = h.id_estante
  WHERE e.id_usuario <> h.id_usuario;
  ```

- **Como interpretar:** qualquer linha indica que a FK foi removida ou desabilitada.

### R3. Produto na estante de quem não o possui

- **Objetivo:** só o seed garante essa regra (ver [pauta, item 2](../pauta-reuniao.md#2-produto-na-estante-de-quem-não-o-possui-produtos_estantes)).
- **Consulta:**

  ```sql
  SELECT pe.id_estante, pe.id_produto, e.id_usuario
  FROM produtos_estantes AS pe
  JOIN estantes AS e ON e.id_estante = pe.id_estante
  LEFT JOIN produtos_usuarios AS pu
         ON pu.id_usuario = e.id_usuario AND pu.id_produto = pe.id_produto
  WHERE pu.id_usuario IS NULL;
  ```

- **Como interpretar:** cada linha é um produto guardado na estante de quem não o possui.

### R6. Produto sem registro de descarte

- **Objetivo:** todo produto tem exatamente um `descartes_fds` (o `UNIQUE` impede mais de um; a consulta procura os que têm zero).
- **Consulta:**

  ```sql
  SELECT p.id_produto, p.nome
  FROM produtos AS p
  LEFT JOIN descartes_fds AS d ON d.id_produto = p.id_produto
  WHERE d.id_produto IS NULL;
  ```

- **Como interpretar:** produtos listados não têm informação de descarte.
