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

Os commits **definem a próxima versão** (veja [Versões e releases](#versões-e-releases)), então escolha o tipo com cuidado.

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

As versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/) e são geradas automaticamente pelo [release-please](https://github.com/googleapis/release-please) a partir dos commits que chegam na `main`:

| Commit | Efeito na versão (antes da 1.0) |
|---|---|
| `fix:` | sobe o número de correção (`0.1.0` → `0.1.1`) |
| `feat:` | sobe o número menor (`0.1.0` → `0.2.0`) |
| `feat!:` ou `BREAKING CHANGE:` | também sobe o número menor, até a versão 1.0 |
| `docs:`, `refactor:`, `perf:` | aparecem no CHANGELOG, sem gerar versão sozinhos |
| `test:`, `chore:` | não aparecem no CHANGELOG |

O release-please mantém aberto um PR chamado **"chore(main): release x.y.z"**, com a versão e o `CHANGELOG.md` (criado no primeiro release). **Mergear esse PR cria a tag e a release no GitHub.** Não edite o CHANGELOG nem a versão à mão.

Para forçar uma versão específica (por exemplo, a 1.0.0), inclua no corpo de um commit a linha `Release-As: 1.0.0`.
