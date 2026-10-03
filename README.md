# data-load-quimia

Carga de dados (seed) para o banco PostgreSQL da **Quimia**, um app de produtos químicos domésticos. O projeto popula os bancos `test` e `main` (dois serviços no Aiven) com dados coerentes, válidos, reproduzíveis e seguros.

O schema do banco é definido por `sql/01_ddl.sql` e `sql/02_fks.sql`, que são a fonte da verdade. **Esses scripts nunca devem ser executados no Aiven**, porque começam com `DROP TABLE ... CASCADE`.

## Instalação (Windows)

Requisitos: [uv](https://docs.astral.sh/uv/) e Python 3.14 (o uv instala, se faltar).

```powershell
uv sync                      # cria .venv e instala dependências + grupo dev
uv run pre-commit install    # ativa os hooks de qualidade no git commit
uv run pre-commit install --hook-type commit-msg   # ativa a verificação da mensagem de commit
```

O grupo `catalog` (httpx) só é necessário para o script offline do catálogo: `uv sync --group catalog`.

## Configuração dos bancos

1. **Certificados:** no console do Aiven (serviço > *Overview* > *CA certificate*), baixe o CA de cada serviço e salve em `certs/ca-test.pem` e `certs/ca-main.pem`. A pasta fica fora do Git.
2. **Allowlist:** em *Overview* > *Allowed IP addresses*, libere o IP da sua máquina nos dois serviços. Sem isso, a conexão termina em timeout.
3. **Variáveis:** `Copy-Item .env.example .env.test` (banco de teste) e `Copy-Item .env.example .env` (banco principal), e preencha host, porta, usuário, senha e caminho do CA de cada serviço (o usuário do serviço, por exemplo `avnadmin`). O alvo padrão é sempre `test`.
4. **Conferência:** `uv run seed check` (test) e `uv run seed --target main check` (main). O comando só lê.

## Comandos principais

```powershell
uv run seed check                    # diagnóstico do banco de teste (somente leitura)
uv run seed --target main check      # diagnóstico do banco principal (somente leitura)
uv run ruff check            # lint
uv run ruff format --check   # formatação
uv run mypy                  # tipos
uv run pytest -m "not integration"   # testes unitários, sem banco
```

## Documentação

Todo o detalhe fica em [`docs/`](docs/README.md):

- [Pauta de reunião: decisões pendentes do schema](docs/pauta-reuniao.md)
- [Decisões tomadas (ADRs)](docs/decisoes/)
- [Observações de modelagem](docs/schema/observacoes-modelagem.md)
- [Consultas de verificação](docs/schema/consultas-verificacao.md)
- [Problemas e soluções](docs/problemas-e-solucoes.md)
