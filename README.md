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

## Comandos principais

```powershell
uv run seed                  # CLI do seed (comandos completos a partir da fase 2)
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
