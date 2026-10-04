# data-load-quimia

Carga de dados (seed) para o banco PostgreSQL da **Quimia**, um app de produtos químicos domésticos. O projeto popula os bancos `test` e `main` (dois serviços no Aiven) com dados coerentes, válidos, reproduzíveis e seguros: 100 registros por tabela.

O schema é definido por `sql/01_ddl.sql` e `sql/02_fks.sql`, que são a fonte da verdade e são gerenciados fora deste projeto. **Esses scripts nunca devem ser executados no Aiven**, porque começam com `DROP TABLE ... CASCADE`.

## Instalação (Windows)

Requisitos: [uv](https://docs.astral.sh/uv/) e Python 3.14 (o uv instala, se faltar).

```powershell
uv sync                                            # cria .venv e instala dependências + grupo dev
uv run pre-commit install                          # hooks de qualidade no git commit
uv run pre-commit install --hook-type commit-msg   # verificação da mensagem de commit
```

## Configuração dos bancos

1. **Certificados:** no console do Aiven (serviço > *Overview* > *CA certificate*), baixe o CA de cada serviço e salve em `certs/ca-test.pem` e `certs/ca-main.pem`. A pasta fica fora do Git.
2. **Allowlist:** em *Service settings* > *Allowed IP addresses*, libere o IP da sua máquina nos dois serviços. Sem isso, a conexão termina em timeout.
3. **Variáveis:** `Copy-Item .env.example .env.test` (banco de teste) e `Copy-Item .env.example .env` (banco principal), e preencha host, porta, usuário, senha e caminho do CA de cada serviço. O alvo padrão é sempre `test`.
4. **Conferência:** `uv run seed check` (test) e `uv run seed --target main check` (main). O comando só lê.

## Comandos

```powershell
uv run seed check                    # diagnóstico do banco de teste (somente leitura)
uv run seed --target main check      # diagnóstico do banco principal (somente leitura)
uv run ruff check                    # lint
uv run ruff format --check           # formatação
uv run mypy                          # tipos
uv run pytest                        # testes unitários (nenhum conecta a banco)
```

Os comandos `validate`, `run`, `reset`, `verificar` e `stats` entram nas próximas etapas.

## Estrutura

| Módulo (`src/seed/`) | Papel |
|---|---|
| `config.py` | Alvos, configuração, conexão, quantidades e formatos das URLs de foto |
| `modelos.py` | Modelos ORM espelhando o DDL e ordem de carga |
| `contratos.py` | Contratos Pydantic por tabela (validação antes do insert) |
| `validacao.py` | Validadores puros: CAS, CNPJ, CEP, coordenadas, URL, idade, fuso |
| `dados.py` | Leitura de `data/reference/` (YAML) e `data/catalog/` (JSON) |
| `generators/` | Dados sintéticos com Faker pt_BR e `random.Random(seed)`, um arquivo por grupo de tabelas: `contas.py`, `produtos.py`, `estantes.py`, `historicos.py` |
| `carga.py` | Inserts em lote (Core + `RETURNING`), registro de IDs, transação única |
| `verificacao.py` | Consultas somente leitura: `check`, `verificar`, `stats` |
| `cli.py` | Linha de comando (Typer) |

Os módulos ficam no nível de `src/seed/`; um módulo vira pasta quando passa de cerca de 300 linhas ou tem partes claramente separadas, como `generators/`.

## Decisões

Decisões já tomadas, com o motivo. As que dependem do time estão em [docs/pauta-reuniao.md](docs/pauta-reuniao.md).

### Ambiente e conexão

- **Sem Docker.** Dois serviços separados no Aiven: `test` (padrão de todos os comandos) e `main` (principal). Serviços separados isolam credenciais, limites e backups.
- **Arquivos de configuração:** `.env.test` para o teste e **`.env` para o principal**, os dois fora do Git. Como o `.env` é carregado automaticamente por várias ferramentas, há duas proteções: o `.vscode/settings.json` não injeta o `.env` no editor, e o alvo `test` aborta se resolver para o mesmo host e porta do `.env`.
- **SSL `verify-ca`**, não `verify-full`: o libpq do `psycopg-binary` para Windows rejeita o endereço IPv6 que o Aiven coloca no certificado (`certificate contains IP address with invalid length 16`). Com `verify-ca`, a conexão continua criptografada e o certificado continua validado contra o CA do projeto; só o nome do host deixa de ser conferido. O risco é baixo, porque cada projeto do Aiven tem um CA próprio. Vale testar `verify-full` de novo quando o `psycopg-binary` trouxer outro libpq.
- **Usuário do serviço** (por exemplo `avnadmin`), sem criar um usuário só para o seed. A proteção do `main` contra apagar dados depende das travas do código, não de privilégios no banco.
- **Pool pequeno** (2 + 1), porque os planos do Aiven têm limite de conexões. O `seed check` mostra versão, conexões abertas, `max_connections` e tamanho do banco.
- **Schema `public`.**

### Schema

- **`sql/` é a fonte da verdade.** O schema é criado e alterado fora deste projeto. O seed nunca executa esses scripts.
- **Sem Alembic.** O projeto não cria nem altera tabelas, então uma ferramenta de migração não tinha função e acrescentava baseline, stamp e credenciais extras. A pauta tem um item sobre como aplicar mudanças de schema nos dois bancos.
- **Modelos ORM (SQLAlchemy 2.0) ficaram**, só para descrever as tabelas: dão a ordem de carga (`metadata.sorted_tables`), a tipagem e a base da comparação com o banco real feita pelo `seed check`. Eles não criam tabelas. Os inserts usam o Core (`insert(Modelo.__table__)` com lista de dicionários e `RETURNING`), nunca `session.add` linha a linha.
- **Contratos Pydantic ficaram**, para validar cada linha antes do insert: tamanhos, valores dos CHECKs, CAS, CNPJ, CEP, e-mail, URL e datas. Um erro aparece com o nome do campo antes de chegar ao banco.
- **Mudança de schema exige atualizar três lugares juntos:** `sql/`, `modelos.py` e `contratos.py`. O `seed check` mostra divergências entre os modelos e o banco, e o `seed run` se recusa a rodar se houver alguma. Um teste unitário confere modelos × DDL e contratos × modelos.
- **Enums só para os CHECKs do DDL** (`status`, `porte`, `acao`); um teste confere os valores contra `sql/01_ddl.sql`. `comodo` e o nome dos tipos de histórico não têm CHECK no banco: os valores válidos ficam em `data/reference`, para mudarem sem alterar código.
- **Datas com fuso nos contratos:** os contratos recusam datas sem fuso ou no futuro. A conversão para o horário sem fuso das colunas `TIMESTAMP` acontece só na carga.
- **CNPJ alfanumérico** (formato da Receita Federal em vigor desde 31/07/2026): 12 caracteres `[0-9A-Z]` e 2 dígitos verificadores numéricos, módulo 11, com cada caractere valendo o código ASCII menos 48. Os CNPJs numéricos continuam válidos. Testado com o exemplo oficial `12.ABC.345/01DE-35`.
- **E-mails sintéticos** só com os domínios reservados `example.com` e `example.org` (lista em `config.py`), em minúsculas.
- **Nenhuma melhoria de schema agora.** Todas estão na pauta para o time decidir.
- **`cas_number` é UNIQUE:** um produto por substância. O catálogo tem 100 substâncias distintas. As alternativas estão na pauta (item 1).
- **Colunas `TIMESTAMP` sem fuso:** as datas são geradas com fuso em `America/Sao_Paulo`, convertidas para `SEED_TIMEZONE` (padrão UTC) e gravadas sem fuso. O `seed check` avisa se o fuso do servidor for diferente, e o `seed run` se recusa a rodar nesse caso.

### Dados

- **100 registros por tabela**, fixos em `config.py` (fácil de mudar). A exceção é `tipos_historicos`, que recebe só os tipos de `data/reference` (cinco). `localizacoes` tem uma por usuário, e `descartes_fds` um por produto.
- **Sem Polyfactory.** Os geradores são funções simples com Faker `pt_BR` e `random.Random`, com uma semente única (`--seed`, padrão 42): a mesma semente gera os mesmos dados. Para 100 linhas por tabela, uma biblioteca de fábricas não trazia vantagem.
- **Tipos de histórico pelo seed**, a partir de `data/reference`, com `ON CONFLICT (nome) DO NOTHING`, nos dois alvos. Valores provisórios: USO, MISTURA, DESCARTE, ARMAZENAMENTO, VERIFICACAO. Cômodos: COZINHA, LAVANDERIA, AREA_SERVICO, BANHEIRO, GARAGEM, DESPENSA, QUARTO, SALA.
- **Regras por tipo de histórico** em YAML: USO, DESCARTE e ARMAZENAMENTO com exatamente 1 produto; VERIFICACAO com 0 a 3; MISTURA com 2 a 4. ARMAZENAMENTO e VERIFICACAO exigem estante. Um ARMAZENAMENTO exige o produto na estante (`produtos_estantes`) com `data_adicao` até a data do histórico.
- **Idade mínima de 18 anos**, calculada na data de cadastro; 10% dos usuários sem `data_nascimento`. Os dois valores ficam em `config.py`.
- **Catálogo de produtos** escrito à mão em `data/catalog`, com CAS reais validados pelo dígito verificador. Toda entrada começa com `"revisado": false` e `"fonte": "pendente de conferência"`, e os campos de descarte com "pendente de revisão". Textos de segurança nunca são inventados.
- **Fotos:** usuários com `https://randomuser.me/api/portraits/{men|women}/{0-99}.jpg`, com o gênero da foto combinando com o nome e sem repetir índice; empresas com `https://ui-avatars.com/api/?name=<nome>&size=256`. A tabela `admins` não tem coluna de foto. Os formatos ficam em `config.py`. **Risco:** são links externos; se um serviço mudar ou sair do ar, as imagens quebram. A pauta tem um item sobre hospedar as imagens.
- **`admin_log_edicoes`:** 100 registros só de INSERT (registro existente, `dado_anterior` nulo, data igual à criação do registro), **somente no `test`**. Auditoria falsa no principal é pior que auditoria vazia.

### Banco principal

- O `main` pode receber dados fictícios (exceto auditoria), só com `--allow-synthetic` e confirmação digitando o nome do banco. Sem a opção, recebe só referência e catálogo revisado.
- `reset` é bloqueado no `main` pelo código. Nada é executado pelo assistente contra o `main`.
- `SEED_PASSWORD_PLAIN` (senha dos usuários fictícios) deve ser diferente em cada arquivo.

## Documentação

- [Pauta de reunião: decisões pendentes](docs/pauta-reuniao.md)
- [Problemas e soluções](docs/problemas-e-solucoes.md)
