# Pauta de reunião: decisões pendentes do schema

Este documento é para quem não acompanhou o desenvolvimento do seed. Cada item descreve uma decisão que o time precisa tomar sobre o banco da Quimia. Nada foi alterado no banco: hoje vale exatamente o que está em `sql/01_ddl.sql` e `sql/02_fks.sql`.

Cada item segue a mesma estrutura:

- **Situação atual:** o que o banco faz hoje.
- **Problema:** o que pode dar errado na prática.
- **Opções:** as alternativas, incluindo manter como está.
- **Impacto:** o que muda no backend, nos dados existentes e no seed.
- **Verificação antes de aplicar:** consulta SQL que mostra se os dados atuais violariam a regra. *Ainda não foi executada.*
- **Recomendação** e **Decisão** (a preencher na reunião).

Os itens estão em ordem de prioridade.

---

## 1. Um produto por substância (`produtos.cas_number` único)

**Situação atual:** a coluna `cas_number` da tabela `produtos` é `UNIQUE`. O CAS number identifica uma **substância química**, não um produto comercial.

**Problema:** duas marcas de água sanitária têm a mesma substância principal (hipoclorito de sódio, CAS 7681-52-9). Hoje o banco só aceita uma delas. Quando a segunda empresa cadastrar o seu produto, o backend recebe um erro de violação de unicidade.

**Opções:**

1. Manter como está.
2. Trocar por `UNIQUE (cas_number, marca)`: a mesma substância pode aparecer em marcas diferentes, mas cada marca só tem um produto por substância.
3. Remover o `UNIQUE` do CAS e criar `UNIQUE (id_usuario_empresa, nome)`: cada empresa não repete o nome de produto; várias empresas podem usar a mesma substância.
4. Criar uma tabela `substancias` (com `cas_number` único) e uma tabela associativa `produtos_substancias`: um produto pode ter várias substâncias, e cada substância aparece uma vez no banco.

**Impacto:**

- Opções 2 e 3: uma migração simples; o backend só precisa tratar o novo erro de duplicidade. Os dados atuais continuam válidos (o único atual é mais restrito que os novos).
- Opção 4: muda o modelo; o backend precisa ler e gravar em duas tabelas novas, e os dados atuais precisam ser migrados (cada produto vira uma linha em `produtos_substancias`). É a mais correta para produtos com várias substâncias.
- Seed: o gerador já está preparado; basta trocar a regra de chave natural e o limite de volume.

**Verificação antes de aplicar** (para a opção 3, a única que pode falhar com os dados atuais):

```sql
SELECT id_usuario_empresa, nome, count(*) AS quantidade
FROM produtos
GROUP BY id_usuario_empresa, nome
HAVING count(*) > 1;
```

Nenhuma linha significa que a nova regra pode ser aplicada.

**Recomendação:** opção 4 a médio prazo, porque produtos de limpeza costumam ter mais de uma substância e a FDS fala de cada uma. Se o time quiser uma mudança pequena agora, opção 2.

**Decisão:**

---

## 2. Produto na estante de quem não o possui (`produtos_estantes`)

**Situação atual:** a tabela `produtos_estantes` liga `id_estante` a `id_produto`, sem `id_usuario`. A tabela `produtos_usuarios` diz quais produtos cada usuário possui.

**Problema:** o banco aceita colocar na estante da Ana um produto que só o Bruno possui. Exemplo: Ana tem a estante 10 (cozinha); o backend, por um bug, grava `(10, produto 55)`, e o produto 55 não está em `produtos_usuarios` para a Ana. A tela da estante da Ana mostraria um produto que não é dela.

**Opções:**

1. Manter como está e garantir a regra só no backend (e no seed, que já garante).
2. Acrescentar `id_usuario` em `produtos_estantes`, com duas FKs compostas: `(id_estante, id_usuario) → estantes` e `(id_usuario, id_produto) → produtos_usuarios`. É o mesmo padrão já usado em `historicos_produtos`.

**Impacto:**

- Backend: passa a enviar `id_usuario` ao guardar um produto na estante.
- Dados existentes: precisam ter o `id_usuario` preenchido a partir de `estantes`; linhas que violam a regra precisam ser corrigidas antes.
- Seed: só acrescenta a coluna.

**Verificação antes de aplicar:**

```sql
SELECT pe.id_estante, pe.id_produto, e.id_usuario
FROM produtos_estantes AS pe
JOIN estantes AS e ON e.id_estante = pe.id_estante
LEFT JOIN produtos_usuarios AS pu
       ON pu.id_usuario = e.id_usuario
      AND pu.id_produto = pe.id_produto
WHERE pu.id_usuario IS NULL;
```

Cada linha retornada é um produto guardado na estante de quem não o possui.

**Recomendação:** opção 2. O banco já faz isso em `historicos_produtos`, e regras de posse não deveriam depender só do backend.

**Decisão:**

---

## 3. E-mail duplicado com maiúsculas diferentes

**Situação atual:** `email` é `UNIQUE` em `admins`, `usuarios` e `usuarios_empresas`, mas a comparação diferencia maiúsculas e minúsculas.

**Problema:** `Ana@gmail.com` e `ana@gmail.com` podem virar duas contas diferentes. Na prática é a mesma caixa de e-mail, e o login ou a recuperação de senha podem cair na conta errada.

**Opções:**

1. Manter como está e o backend sempre converter para minúsculas antes de gravar.
2. Criar um índice único em `lower(email)` nas três tabelas.
3. Usar o tipo `citext` (extensão do Postgres) na coluna `email`.

**Impacto:**

- Opção 2: uma migração simples; o backend não muda, mas passa a receber erro de duplicidade nesses casos.
- Opção 3: exige habilitar a extensão `citext` e alterar o tipo da coluna.
- Dados existentes: duplicatas precisam ser resolvidas antes.
- Seed: já gera e-mails em minúsculas.

**Verificação antes de aplicar** (repetir trocando `usuarios` por `admins` e `usuarios_empresas`):

```sql
SELECT lower(email) AS email_normalizado, count(*) AS quantidade
FROM usuarios
GROUP BY lower(email)
HAVING count(*) > 1;
```

**Recomendação:** opção 2, junto com a normalização no backend.

**Decisão:**

---

## 4. Formato do CEP (`localizacoes.cep`)

**Situação atual:** `cep` é `VARCHAR(8) NOT NULL`, sem verificação de formato.

**Problema:** o banco aceita `"1310-100"`, `"ABCDEFGH"` ou `"123"`. Um CEP com máscara (`"01310-100"`) nem cabe em 8 caracteres e daria erro; um CEP incompleto passaria e quebraria a busca de endereço.

**Opções:**

1. Manter como está.
2. Criar `CHECK (cep ~ '^[0-9]{8}$')`: só 8 dígitos, sem máscara.

**Impacto:**

- Backend: **conferir se envia o CEP com máscara** (com hífen). Se enviar, precisa remover a máscara antes de gravar.
- Dados existentes: linhas fora do formato precisam ser corrigidas antes.
- Seed: já grava só 8 dígitos.

**Verificação antes de aplicar:**

```sql
SELECT id_localizacao, cep
FROM localizacoes
WHERE cep !~ '^[0-9]{8}$';
```

**Recomendação:** opção 2, depois de confirmar o formato que o backend envia.

**Decisão:**

---

## 5. Índices nas colunas de chave estrangeira

**Situação atual:** o Postgres cria índice automático para PKs e UNIQUEs, mas **não** para colunas de FK. Colunas como `historicos.id_usuario`, `produtos.id_usuario_empresa` e `estantes.id_usuario` não têm índice próprio (algumas ficam cobertas por um UNIQUE composto que começa por elas).

**Problema:** a consulta "históricos do usuário 42" lê a tabela inteira. Com poucos dados, ninguém percebe; com milhares de usuários, as telas ficam lentas. Apagar um usuário também força uma leitura completa de cada tabela filha.

**Opções:**

1. Manter como está.
2. Criar índices nas colunas de FK que não estejam cobertas por outro índice.

**Impacto:**

- Backend: nenhum.
- Dados: nenhum. Os índices ocupam espaço em disco e deixam inserts um pouco mais lentos.
- Seed: nenhum.

**Verificação antes de aplicar** (lista as FKs sem índice cujas primeiras colunas sejam as da FK):

```sql
SELECT c.conrelid::regclass AS tabela,
       c.conname           AS fk,
       pg_get_constraintdef(c.oid) AS definicao
FROM pg_constraint AS c
WHERE c.contype = 'f'
  AND c.connamespace = 'public'::regnamespace
  AND NOT EXISTS (
        SELECT 1
        FROM pg_index AS i
        WHERE i.indrelid = c.conrelid
          AND (string_to_array(i.indkey::text, ' ')::int2[])[1:cardinality(c.conkey)] @> c.conkey
          AND (string_to_array(i.indkey::text, ' ')::int2[])[1:cardinality(c.conkey)] <@ c.conkey
      );
```

**Recomendação:** opção 2. É a mudança de menor risco da pauta.

**Decisão:**

---

## 6. Datas sem fuso horário (`TIMESTAMP` versus `TIMESTAMPTZ`)

**Situação atual:** todas as colunas de data e hora (`data_cadastro`, `data_execucao`, `data_adicao`, `data_edicao`) são `TIMESTAMP` sem fuso, com `DEFAULT CURRENT_TIMESTAMP`.

**Problema:**

- O `DEFAULT CURRENT_TIMESTAMP` grava o horário **no fuso da sessão** que fez o insert. Se o backend conecta com fuso `America/Sao_Paulo` e o seed com `UTC`, registros criados no mesmo instante ficam com **3 horas de diferença**.
- O valor gravado não diz em que fuso está. Depois de gravado, não há como saber se `2026-10-03 14:00` é horário de Brasília ou UTC.

**Opções:**

1. Manter `TIMESTAMP` e combinar um fuso único para todas as conexões (backend, seed, ferramentas).
2. Migrar para `TIMESTAMPTZ`: o Postgres guarda o instante absoluto e converte na leitura. Elimina o problema.

**Impacto:**

- Opção 2: a migração precisa dizer em que fuso estão os dados atuais (`ALTER COLUMN ... TYPE timestamptz USING data_cadastro AT TIME ZONE '<fuso>'`). O backend passa a receber datas com fuso.
- Seed: já gera datas com fuso e converte para o fuso configurado ([ADR 0010](decisoes/0010-fuso-horario-das-colunas-timestamp.md)).

**Pergunta para o time:** o backend configura o fuso da sessão ao conectar? Qual?

**Verificação antes de aplicar** (mostra o fuso do servidor e o que cada função devolve):

```sql
SHOW timezone;
SELECT now() AS agora_com_fuso, localtimestamp AS agora_sem_fuso;
```

**Recomendação:** opção 2. Enquanto isso, opção 1 com UTC em todas as conexões.

**Decisão:**

---

## 7. Snapshot da auditoria como texto (`admin_log_edicoes.dado_anterior`)

**Situação atual:** `dado_anterior` é `TEXT`. O seed grava ali o JSON da linha antes da edição.

**Problema:** o banco não garante que o conteúdo seja um JSON válido e não permite consultar dentro dele. Exemplo: "quais edições mudaram o status de um usuário de ATIVO para BLOQUEADO?" exige ler e interpretar cada texto fora do banco.

**Opções:**

1. Manter `TEXT`.
2. Trocar por `JSONB`: garante JSON válido e permite consultas como `dado_anterior->>'status'`.

**Impacto:**

- Backend: passa a enviar JSON (a maioria das bibliotecas já faz isso).
- Dados existentes: textos que não são JSON válido impedem a migração e precisam ser corrigidos antes.
- Seed: só troca o tipo.

**Verificação antes de aplicar** (Postgres 16 ou mais recente):

```sql
SELECT id_admin_log_edicao, left(dado_anterior, 80) AS inicio
FROM admin_log_edicoes
WHERE dado_anterior IS NOT NULL
  AND dado_anterior IS NOT JSON;
```

**Recomendação:** opção 2.

**Decisão:**

---

## 8. Limite de 255 caracteres em `historicos.descricao_resultado`

**Situação atual:** `descricao_resultado` é `VARCHAR(255)`.

**Problema:** um resultado mais detalhado é cortado pelo backend ou recusado pelo banco.

**Opções:**

1. Manter 255.
2. Trocar por `TEXT` (no Postgres, `TEXT` e `VARCHAR` têm o mesmo desempenho).
3. Aumentar o limite (por exemplo, 1000).

**Impacto:** migração simples, sem efeito nos dados atuais. O backend só precisa ajustar a validação de tamanho.

**Verificação antes de aplicar** (mostra se os textos já estão perto do limite):

```sql
SELECT max(length(descricao_resultado)) AS maior,
       count(*) FILTER (WHERE length(descricao_resultado) >= 240) AS perto_do_limite
FROM historicos;
```

**Recomendação:** opção 2, mantendo um limite de tamanho só no backend, onde é fácil mudar.

**Decisão:**

---

## 9. Coordenadas aceitam qualquer ponto do planeta

**Situação atual:** em `localizacoes`, `latitude` aceita −90 a 90 e `longitude` −180 a 180, e as duas aceitam nulo.

**Problema:** o app é para o Brasil, mas o banco aceita uma coordenada em Tóquio. Uma troca de latitude por longitude no backend passaria sem erro.

**Opções:**

1. Manter como está.
2. Restringir à faixa do Brasil (latitude −33,8 a 5,3; longitude −74,0 a −34,8).
3. Manter a faixa global e validar a do Brasil só no backend.

**Impacto:** a opção 2 bloqueia usuários fora do país, se o app um dia aceitar. Os dados fora da faixa precisam ser corrigidos antes.

**Verificação antes de aplicar:**

```sql
SELECT id_localizacao, latitude, longitude
FROM localizacoes
WHERE latitude  NOT BETWEEN -33.8 AND 5.3
   OR longitude NOT BETWEEN -74.0 AND -34.8;
```

**Recomendação:** opção 3, a não ser que o produto seja oficialmente só para o Brasil.

**Decisão:**

---

## 10. Data de nascimento nula versus idade mínima

**Situação atual:** `usuarios.data_nascimento` aceita nulo. O app pretende exigir idade mínima de 18 anos. O seed deixa 10% dos usuários sem data e calcula a idade na data de cadastro ([ADR 0006](decisoes/0006-idade-minima-e-data-nascimento.md)).

**Problema:** se o usuário não informou a data, não há como verificar a idade mínima.

**Perguntas para o time:**

- O campo deveria ser obrigatório?
- Qual é a idade mínima oficial? Ela está nos termos de uso?
- Para usuários antigos sem data, o que fazer: pedir no próximo login ou bloquear?

**Opções:**

1. Manter opcional e verificar só quando informada.
2. Tornar `NOT NULL` e criar um CHECK de idade mínima no cadastro.

**Impacto:** a opção 2 exige que todos os usuários atuais tenham a data preenchida, e o backend passa a exigir o campo no cadastro. No seed, basta mudar a fração de nulos para 0 no perfil.

**Verificação antes de aplicar:**

```sql
SELECT count(*) FILTER (WHERE data_nascimento IS NULL) AS sem_data,
       count(*) FILTER (WHERE age(data_cadastro::date, data_nascimento) < interval '18 years') AS menores_no_cadastro
FROM usuarios;
```

**Recomendação:** opção 2, se a idade mínima estiver nos termos de uso.

**Decisão:**

---

## 11. Lista oficial de tipos de histórico e suas regras

**Situação atual:** a tabela `tipos_historicos` não tem valores oficiais. O seed usa uma lista provisória, com uma regra por tipo ([ADR 0007](decisoes/0007-regras-por-tipo-de-historico.md)):

| Tipo | Produtos no histórico | Estante |
|---|---|---|
| USO | exatamente 1 | opcional |
| DESCARTE | exatamente 1 | opcional |
| ARMAZENAMENTO | exatamente 1 | obrigatória |
| VERIFICACAO | 0 a 3 | obrigatória |
| MISTURA | 2 a 4 | opcional |

**Problema:** o backend e o seed podem divergir sobre os tipos e as regras. Exemplo: o backend grava um histórico de MISTURA com um só produto, e as telas que esperam dois quebram.

**Perguntas para o time:**

- A lista está completa e com os nomes certos?
- As regras de quantidade de produtos e de estante estão corretas?
- Um ARMAZENAMENTO deveria criar automaticamente a linha em `produtos_estantes`?

**Opções:**

1. Confirmar a lista e as regras como estão.
2. Alterar a lista e as regras. No seed, basta editar o arquivo YAML em `data/reference/`.

**Impacto:** os tipos entram no banco por migração; a lista final vira uma nova migração.

**Verificação antes de aplicar** (quantos produtos cada tipo tem hoje):

```sql
SELECT t.nome,
       count(DISTINCT h.id_historico) AS historicos,
       min(qtd.n) AS min_produtos,
       max(qtd.n) AS max_produtos
FROM tipos_historicos AS t
LEFT JOIN historicos AS h ON h.id_tipo_historico = t.id_tipo_historico
LEFT JOIN LATERAL (
    SELECT count(*) AS n
    FROM historicos_produtos AS hp
    WHERE hp.id_historico = h.id_historico
) AS qtd ON true
GROUP BY t.nome
ORDER BY t.nome;
```

**Recomendação:** confirmar com o time de produto antes da primeira carga no `main`.

**Decisão:**

---

## 12. Quem escreve a auditoria (`admin_log_edicoes`)

**Situação atual:** a tabela registra edições feitas por admins: tabela afetada, ID do registro, ação (INSERT, UPDATE, DELETE), JSON anterior e data. `id_admin` é `NOT NULL`. O seed popula essa tabela **só no banco de teste** ([ADR 0008](decisoes/0008-admin-log-somente-no-test.md)).

**Perguntas para o time:**

1. Quem escreve essa tabela no app real: o backend ou um trigger no banco?
2. Quais tabelas são auditadas? O seed usa provisoriamente: `usuarios`, `usuarios_empresas`, `produtos`, `descartes_fds` e `tipos_historicos`.
3. Se for por trigger, como ele descobre o `id_admin`, que é obrigatório? (Por exemplo, o backend definindo uma variável de sessão com `SET LOCAL app.id_admin = ...`.)
4. Se um trigger for criado no futuro, ele também registraria os inserts feitos pelo seed? Nesse caso, o seed precisaria de um admin técnico ou de uma forma de desligar a auditoria durante a carga.

**Opções:**

1. Auditoria pelo backend (mais simples, mas qualquer acesso direto ao banco fica sem registro).
2. Auditoria por trigger (registra tudo, mas exige resolver o `id_admin`).

**Impacto:** a opção 2 exige uma migração com o trigger e uma mudança no backend para informar o admin. O seed precisa tratar o trigger durante a carga.

**Verificação antes de aplicar** (o que existe hoje):

```sql
SELECT tabela_afetada, acao, count(*) AS quantidade
FROM admin_log_edicoes
GROUP BY tabela_afetada, acao
ORDER BY tabela_afetada, acao;

SELECT event_object_table AS tabela, trigger_name
FROM information_schema.triggers
WHERE trigger_schema = 'public';
```

**Recomendação:** opção 1 por enquanto, com a lista de tabelas auditadas definida pelo time.

**Decisão:**

---

## Resumo para slide

| # | Item | Risco de aplicar | Quem é afetado | Recomendação |
|---|---|---|---|---|
| 1 | CAS único em produtos | Médio a alto (opção 4 muda o modelo) | Backend, dados, seed | Tabela de substâncias (ou `UNIQUE (cas, marca)` agora) |
| 2 | `produtos_estantes` sem `id_usuario` | Médio (exige corrigir dados) | Backend, dados | Acrescentar `id_usuario` e FKs compostas |
| 3 | E-mail único sem diferenciar maiúsculas | Baixo | Dados | Índice único em `lower(email)` |
| 4 | Formato do CEP | Baixo (conferir máscara) | Backend, dados | CHECK de 8 dígitos |
| 5 | Índices nas FKs | Muito baixo | Ninguém | Criar os índices |
| 6 | TIMESTAMP sem fuso | Médio (converter dados) | Backend, dados | Migrar para TIMESTAMPTZ |
| 7 | `dado_anterior` como TEXT | Baixo | Backend | Trocar para JSONB |
| 8 | Limite de 255 em `descricao_resultado` | Muito baixo | Backend | Trocar para TEXT |
| 9 | Coordenadas fora do Brasil | Baixo | Backend | Validar no backend |
| 10 | `data_nascimento` nula | Médio (usuários sem data) | Produto, backend, dados | Obrigatória, se estiver nos termos |
| 11 | Tipos de histórico e regras | Baixo | Produto, backend | Confirmar a lista |
| 12 | Quem escreve a auditoria | Médio | Backend, seed | Backend, com tabelas definidas |

## Como uma decisão vira mudança no banco

Cada mudança aprovada vira uma **migração do Alembic** (um arquivo versionado que altera o banco de forma controlada) e, no mesmo commit, a atualização dos scripts `sql/01_ddl.sql` e `sql/02_fks.sql`. O **teste de paridade** do projeto compara o schema criado pelos scripts com o schema dos modelos Python e falha se os dois divergirem, então o DDL e o código nunca ficam desalinhados. A migração é aplicada primeiro no banco de teste; no banco principal, o SQL é revisado e executado por uma pessoa.
