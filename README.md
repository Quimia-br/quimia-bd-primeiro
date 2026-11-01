# data-load-quimia

Carga de dados (seed) para o banco PostgreSQL da **Quimia**, um app de produtos químicos domésticos. O projeto popula os bancos `test` e `main` (dois serviços no Aiven) com dados coerentes, válidos, reproduzíveis e seguros: 100 registros por tabela.

O schema é definido por `sql/01_ddl.sql` e `sql/02_fks.sql`, que são a fonte da verdade e são gerenciados fora deste projeto. **Esses scripts nunca devem ser executados no Aiven**, porque começam com `DROP TABLE ... CASCADE`.

## Instalação

Requisitos: [uv](https://docs.astral.sh/uv/getting-started/installation/) (Windows, macOS ou Linux), Git e Python 3.14 (o uv instala, se faltar).

Os comandos abaixo funcionam igual em PowerShell, Bash e Zsh. Quando um comando muda de um sistema para outro, o README mostra a versão de cada um.

```bash
uv sync                                            # cria .venv e instala dependências + grupo dev
uv run pre-commit install                          # hooks de qualidade no git commit
uv run pre-commit install --hook-type commit-msg   # verificação da mensagem de commit
```

## Configuração dos bancos

1. **Certificados:** no console do Aiven (serviço > *Overview* > *CA certificate*), baixe o CA de cada serviço e salve em `certs/ca-test.pem` e `certs/ca-main.pem`. A pasta fica fora do Git.
2. **Allowlist:** em *Service settings* > *Allowed IP addresses*, libere o IP da sua máquina nos dois serviços. Sem isso, a conexão termina em timeout.
3. **Variáveis:** copie o modelo `.env.example` para `.env.test` (banco de teste) e para `.env` (banco principal), e preencha host, porta, usuário, senha e caminho do CA de cada serviço. O alvo padrão é sempre `test`.

   | Sistema | Comando |
   |---|---|
   | Windows (PowerShell) | `Copy-Item .env.example .env.test` e `Copy-Item .env.example .env` |
   | macOS e Linux | `cp .env.example .env.test` e `cp .env.example .env` |
4. **Conferência:** `uv run seed check` (test) e `uv run seed --target main check` (main). O comando só lê.

## Comandos

```bash
# Somente leitura
uv run seed validate                 # valida data/reference e data/catalog (não conecta)
uv run seed check                    # diagnóstico + comparação modelos × banco (test)
uv run seed --target main check      # o mesmo no banco principal
uv run seed verificar                # regras de negócio: aprovada/reprovada por regra
uv run seed stats                    # linhas por tabela

# Carga (alvo test por padrão)
uv run seed run --dry-run            # gera e valida tudo, sem conectar nem gravar
uv run seed reset                    # esvazia as 13 tabelas (só no test, pede confirmação)
uv run seed run --seed 42            # carga completa numa única transação

# Qualidade
uv run ruff check                    # lint
uv run ruff format --check           # formatação
uv run mypy                          # tipos
uv run pytest                        # testes unitários (nenhum conecta a banco)
```

Códigos de saída: 0 ok, 1 erro, 2 uso inválido, 3 configuração, 4 conexão, 5 dados, 6 modelos × banco divergentes, 7 bloqueado por trava, 8 regra reprovada.

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
| `verificacao/` | Consultas somente leitura: `diagnostico.py` (servidor), `schema.py` (modelos × banco), `regras.py` (regras de negócio e contagens) |
| `cli/` | Linha de comando (Typer): `app.py`, `consulta.py` (comandos de leitura), `escrita.py` (`run` e `reset`), `auxiliares.py` |

Os módulos ficam no nível de `src/seed/`; um módulo vira pasta quando passa de cerca de 300 linhas ou tem partes claramente separadas, como `generators/`, `verificacao/` e `cli/`.

## Decisões

As decisões técnicas do projeto (ambiente e conexão, schema, dados, geradores, carga e proteção do banco principal) estão registradas, com contexto e consequências, em [docs/adr/](docs/adr/README.md).
