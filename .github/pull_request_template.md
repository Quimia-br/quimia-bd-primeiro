## O que muda

<!-- Resuma a mudança em poucas linhas. -->

## Por quê

<!-- Qual problema isso resolve? Link para issue, se houver. -->

## Tipo de mudança

- [ ] `feat`: nova funcionalidade
- [ ] `fix`: correção de erro
- [ ] `refactor` / `perf`
- [ ] `docs`
- [ ] `test` / `chore`

## Checklist

- [ ] O título do PR segue o [Conventional Commits](https://www.conventionalcommits.org/) (`feat: ...`, `fix: ...`).
- [ ] O PR é para a `develop` (ou `develop` → `main`, no caso de release).
- [ ] `uv run ruff check`, `uv run mypy` e `uv run pytest` passam em `dataload/`.
- [ ] Se mudou o schema: atualizei `database/sql/`, `modelos.py` e `contratos.py` juntos.
- [ ] Se tomei uma decisão técnica: registrei ou atualizei um ADR em `dataload/docs/adr/`.
- [ ] Atualizei a documentação afetada (README, ADRs).
- [ ] Não incluí senhas, hosts, certificados nem conteúdo de `.env`.
- [ ] Nenhum comando foi executado contra o banco principal (`main`) por automação.
