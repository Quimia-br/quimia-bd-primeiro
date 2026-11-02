# Como contribuir

Obrigado por querer ajudar no **Quimia · Banco de Dados e Carga**. Este guia explica o fluxo de trabalho do repositório. Para instalar e rodar o projeto, veja o [README](README.md).

Ao participar, você concorda em seguir o [Código de Conduta](CODE_OF_CONDUCT.md). Para reportar uma vulnerabilidade, veja a [Política de Segurança](SECURITY.md) e **não abra uma issue pública**.

## Estrutura do repositório

| Pasta | O que é |
|---|---|
| [`database/`](database/README.md) | Schema PostgreSQL (`sql/`), modelagem e convenção de nomenclatura |
| [`dataload/`](dataload/README.md) | Ferramenta de carga `seed`, em Python, com testes e os [ADRs](dataload/docs/adr/README.md) |

Todos os comandos `uv` rodam dentro de `dataload/`.

## Fluxo de branches

1. A `main` é a versão estável e a `develop` é onde o trabalho se junta. Parta sempre da `develop` atualizada.
2. Cada trabalho vai numa **branch própria**, com o prefixo do tipo: `feat/`, `fix/`, `refactor/`, `test/`, `docs/` ou `chore/`.
3. Abra o PR para a `develop`. Ela vai para a `main` por um PR de `develop` → `main`.
4. Mergeie com **"Create a merge commit"**, para preservar o histórico.
5. Nunca faça commit direto na `main` nem na `develop`.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/), no imperativo e em português:

```
feat: adiciona validação de CEP por faixa de cidade
fix: corrige a ordem de inserção de admin_log_edicoes
docs: explica o fluxo de revisão do catálogo
```

Tipos: `feat`, `fix`, `refactor`, `perf`, `docs`, `test` e `chore`. Um `!` depois do tipo (`feat!:`) ou o rodapé `BREAKING CHANGE:` marca uma mudança incompatível.

O tipo do commit ajuda a escolher a próxima versão e a escrever as notas do release (veja [Versões e releases](#versões-e-releases)), então escolha-o com cuidado.

## Antes de abrir o PR

Instale os hooks uma vez, dentro de `dataload/`:

```bash
uv sync
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

Depois confira:

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest
```

O mesmo conjunto de hooks do pre-commit roda no GitHub em todo PR. Se ele falhar, rode `uv run pre-commit run --all-files` e corrija o que for apontado.

### Mudou o schema?

Atualize **no mesmo commit**:

1. `database/sql/` (fonte da verdade);
2. `dataload/src/seed/modelos.py`;
3. `dataload/src/seed/contratos.py`.

Rode `uv run pytest` e, no banco de teste, `uv run seed check` para confirmar que modelos e banco batem. Nunca execute os scripts de `database/sql/` no Aiven: eles começam com `DROP TABLE ... CASCADE`.

### Tomou uma decisão técnica?

Registre num ADR novo em [`dataload/docs/adr/`](dataload/docs/adr/README.md), com Contexto, Decisão e Consequências, e acrescente-o ao índice. Uma decisão que mudar ganha um novo ADR que substitui o anterior.

## Regras de segurança

- **Nunca** coloque senhas, hosts, certificados, chaves ou o conteúdo de `.env`, `.env.test` e `certs/` em código, testes, logs, commits, issues ou PRs.
- Os dados do seed são sintéticos: e-mails só em `example.com` e `example.org`, e nenhum dado pessoal real.
- Não invente informação química. Textos de descarte, precaução e restrição vêm de fonte conferida (FDS/FISPQ) e ficam "pendente de revisão" até lá.
- O `reset` é bloqueado no banco principal e a carga sintética no `main` exige as travas descritas no README. **Nenhuma automação (GitHub Actions, scripts agendados, assistentes de IA) executa comandos contra o banco principal.**
- Não inclua linhas de coautoria de assistentes de IA nas mensagens de commit; o hook `commit-msg` as rejeita.

## Versões e releases

As versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/) (`MAJOR.MINOR.PATCH`) e os releases são criados **manualmente** por quem mantém o projeto, a partir da `main`:

| O que entrou desde o último release | Versão (antes da 1.0) |
|---|---|
| Só correções (`fix:`) | sobe o número de correção (`0.1.0` → `0.1.1`) |
| Novidades (`feat:`) ou mudança incompatível (`feat!:`, `BREAKING CHANGE:`) | sobe o número menor (`0.1.0` → `0.2.0`) |
| Só documentação, testes ou manutenção | normalmente não gera release |

Para criar um release:

1. No GitHub, abra **Releases → Draft a new release**.
2. Em **Choose a tag**, crie uma tag nova no formato `vX.Y.Z` (por exemplo, `v0.1.0`), apontando para a `main`.
3. Clique em **Generate release notes**: o GitHub lista os PRs mergeados desde o release anterior.
4. Revise o texto e clique em **Publish release**.
