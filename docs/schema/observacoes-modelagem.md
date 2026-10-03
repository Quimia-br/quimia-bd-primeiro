# Observações sobre a modelagem (DDL atual)

Problemas e limitações encontrados em `sql/01_ddl.sql` e `sql/02_fks.sql`. Nada aqui foi alterado no banco (ver [ADR 0005](../decisoes/0005-nenhuma-melhoria-de-schema-agora.md)). Os itens que dependem de decisão do time estão na [pauta](../pauta-reuniao.md).

## Limitações que viram itens de pauta

| # | Tabela / coluna | Limitação | Pauta |
|---|---|---|---|
| 1 | `produtos.cas_number` | `UNIQUE` impede dois produtos com a mesma substância (duas marcas de água sanitária). | item 1 |
| 2 | `produtos_estantes` | Não tem `id_usuario`; o banco não impede guardar na estante um produto que o dono não possui. | item 2 |
| 3 | `email` em `admins`, `usuarios`, `usuarios_empresas` | `UNIQUE` diferencia maiúsculas: `Ana@x.com` e `ana@x.com` coexistem. | item 3 |
| 4 | `localizacoes.cep` | Sem CHECK de formato; aceita máscara, letras ou menos de 8 dígitos. | item 4 |
| 5 | Todas as FKs | O Postgres não cria índice para colunas de FK; joins e `DELETE` no pai ficam lentos com volume. | item 5 |
| 6 | Todas as colunas de data | `TIMESTAMP` sem fuso; o `DEFAULT CURRENT_TIMESTAMP` grava no fuso da sessão. | item 6 |
| 7 | `admin_log_edicoes.dado_anterior` | `TEXT` em vez de `JSONB`; não dá para consultar o conteúdo nem garantir JSON válido. | item 7 |
| 8 | `historicos.descricao_resultado` | `VARCHAR(255)` limita o texto. | item 8 |
| 9 | `localizacoes.latitude/longitude` | CHECKs aceitam o planeta inteiro, não só o Brasil; as duas aceitam nulo. | item 9 |
| 10 | `usuarios.data_nascimento` | Aceita nulo, mas o app pretende exigir idade mínima. | item 10 |
| 11 | `admin_log_edicoes.id_admin` | `NOT NULL`: um trigger não teria como saber o admin sem configuração extra. | item 12 |

## Fatos do schema que o seed precisa respeitar

- **`GENERATED ALWAYS AS IDENTITY`** em todas as PKs simples: o banco recusa IDs informados no `INSERT`. O seed nunca envia as colunas `id_*` de identidade e obtém os IDs com `RETURNING`.
- **FKs compostas com `MATCH SIMPLE`** (o padrão): em `historicos`, se `id_estante` for nulo, a FK `fk_historico_estante` não é verificada; se for preenchido, a estante precisa ser do mesmo usuário.
- **`estantes` tem `UNIQUE (id_estante, id_usuario)`**, redundante com a PK, mas necessário como alvo da FK composta de `historicos`.
- **`historicos` tem `UNIQUE (id_historico, id_usuario)`** pelo mesmo motivo, como alvo da FK composta de `historicos_produtos`.
- **Constraints sem nome** (PKs e UNIQUEs inline) recebem os nomes padrão do Postgres: `<tabela>_pkey` e `<tabela>_<colunas>_key`. Os modelos SQLAlchemy reproduzem esse padrão com uma `naming_convention`.
- **`chk_status` e `chk_url_foto` se repetem** em várias tabelas. É permitido, porque o nome de uma CHECK é único por tabela, não por schema.
- **`estantes.comodo`** não tem CHECK; o default é `'DESCONHECIDO'`. Os valores válidos ficam só no seed ([ADR 0012](../decisoes/0012-valores-de-comodo-e-tipos-de-historico.md)).
- **O DDL começa com `DROP TABLE ... CASCADE`**, por isso nunca é executado no Aiven ([ADR 0003](../decisoes/0003-sql-como-fonte-da-verdade.md)).
