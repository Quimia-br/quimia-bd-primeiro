# dataload

Ferramenta de carga (`seed`) do **Quimia**: uma linha de comando em Python que popula os bancos `test` e `main` no Aiven com 100 registros por tabela, gerados de forma determinística e validados antes de chegar ao banco.

O schema que ela usa está em [`../database/sql/`](../database/README.md). Todos os comandos `uv` rodam **dentro desta pasta**.

```bash
uv sync                  # instala dependências + grupo dev
uv run seed validate     # valida data/reference e data/catalog (não conecta)
uv run seed run --dry-run
uv run pytest
```

| Assunto | Onde está |
|---|---|
| Instalação, configuração dos bancos, comandos, travas de segurança e testes | [README da raiz](../README.md) |
| Decisões de projeto (ADRs) | [`docs/adr/`](docs/adr/README.md) |
| Dados de referência e catálogo | [`data/`](data) |

> [!IMPORTANT]
> Os arquivos `.env.test`, `.env` e a pasta `certs/` ficam **aqui**, em `dataload/`, e nunca vão para o Git.
