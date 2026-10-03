# Problemas e soluções

Cada entrada registra um erro real encontrado no projeto: sintoma, causa, solução e, quando houver, prevenção.

---

## `uv add` falhava ao instalar qualquer biblioteca

- **Sintoma:** `uv add <lib>` e `uv sync` falhavam ao construir o próprio projeto.
- **Causa:** o `uv init --package` cria `src/data_load_quimia/`, e o backend `uv_build` procura o módulo com o nome do projeto (`-` vira `_`). A pasta foi substituída por `src/seed/`, mas o `pyproject.toml` não foi ajustado. O entry point também apontava para `data_load_quimia:main`.
- **Solução:** `[tool.uv.build-backend] module-name = "seed"` e entry point `seed = "seed.cli:main"`.
- **Prevenção:** ao renomear o pacote em `src/`, atualizar `module-name` e `[project.scripts]` juntos.

## pre-commit cancelou o commit por causa do `end-of-file-fixer`

- **Sintoma:** o commit foi abortado com `fix end of files ... Failed - files were modified by this hook`, listando `.gitattributes` e `.gitignore`.
- **Causa:** os arquivos não terminavam com uma quebra de linha. O hook corrige o arquivo, mas cancela o commit para você revisar a correção.
- **Solução:** adicionar os arquivos de novo (`git add .gitattributes .gitignore`) e repetir o commit.
- **Prevenção:** `"files.insertFinalNewline": true` em `.vscode/settings.json`, para o editor já salvar com a quebra de linha final.

## Configurações do editor em `.cursor/settings.json`

- **Sintoma:** as configurações (format on save com Ruff, interpretador da `.venv`) estavam em `.cursor/settings.json`, que também estava fora do Git.
- **Causa:** o Cursor não lê `.cursor/settings.json` como configuração de projeto. A pasta `.cursor/` é usada para regras e outros recursos do próprio Cursor; as configurações de workspace ficam em `.vscode/settings.json`.
- **Solução:** o conteúdo foi movido (não copiado) para `.vscode/settings.json`, que é versionado (`!.vscode/settings.json` no `.gitignore`), e o arquivo antigo foi apagado para não existirem dois arquivos que podem divergir.

## `[ERROR] Your pre-commit configuration is unstaged`

- **Sintoma:** `git commit` abortou com essa mensagem antes de rodar qualquer hook.
- **Causa:** o `.pre-commit-config.yaml` tinha alterações que não estavam no stage. O pre-commit se recusa a rodar com uma configuração diferente da que vai ser commitada.
- **Solução:** `git add .pre-commit-config.yaml` e repetir o commit.

## Commits com linha de coautoria do Claude

- **Sintoma:** os commits `chore: move scripts SQL...`, `chore: ajusta dependências e lint` e `docs: estrutura de documentação...` terminavam com `Co-Authored-By: Claude ... <noreply@anthropic.com>`.
- **Causa:** o Claude Code acrescenta essa linha às mensagens de commit por padrão, e nada no projeto impedia.
- **Solução:** os três commits ainda não tinham sido enviados ao remoto. As mensagens foram reescritas com `git filter-branch --msg-filter` sobre o intervalo `origin/feat/folder-structure..feat/folder-structure`, removendo a linha e a linha em branco que sobrava no fim. O código (hash da árvore), o autor, as datas e a ordem dos commits ficaram iguais; só os hashes dos commits mudaram. Nenhum commit já enviado tinha a linha.
- **Prevenção, em três camadas:**
  1. **Configuração `attribution`** em `.claude/settings.local.json` (fora do Git), com `commit` e `pr` vazios: o Claude Code deixa de gerar a linha. O mesmo arquivo nega `git push` e a leitura de `.env*` e `certs/`.
  2. **Regra no `CLAUDE.md`** (arquivo local, fora do Git): nunca incluir `Co-Authored-By`, "Generated with Claude Code" nem links de sessão, e nunca fazer push.
  3. **Hook `commit-msg`** no `.pre-commit-config.yaml` (`sem-coautoria-claude`, `language: pygrep`): rejeita a mensagem se ela tiver essas linhas, sem diferenciar maiúsculas. O `pre-commit install` padrão só instala o hook `pre-commit`; este exige `uv run pre-commit install --hook-type commit-msg` em cada clone.

## Hooks de espaço em branco alteravam os scripts `sql/`

- **Sintoma:** ao commitar `sql/01_ddl.sql` e `sql/02_fks.sql`, o hook `mixed-line-ending` trocou CRLF por LF, e o `trailing-whitespace` também alteraria linhas com espaço no fim (por exemplo, `CREATE TABLE usuarios(   `).
- **Causa:** os scripts foram salvos no Windows com CRLF e têm espaços no fim de algumas linhas.
- **Solução:** a troca CRLF → LF foi aceita, porque o `.gitattributes` (`* text=auto eol=lf`) já normalizaria no repositório; foi conferido com `git diff --ignore-cr-at-eol` que nada mais mudou. Os hooks `trailing-whitespace` e `end-of-file-fixer` excluem `sql/0[12]_*.sql`, para os scripts continuarem iguais aos entregues.

## mypy não analisava os testes: `module is installed, but missing library stubs or py.typed marker`

- **Sintoma:** `uv run mypy tests` acusava `import-untyped` em todo `import seed...`.
- **Causa:** pela PEP 561, o mypy só usa os tipos de um pacote instalado se ele tiver o arquivo marcador `py.typed`. O `src/seed` não tinha.
- **Solução:** criar `src/seed/py.typed` (vazio) e incluir `tests` em `[tool.mypy] files`, para os testes também serem checados no `uv run mypy`, no pre-commit e no CI.

## Acentos quebrados na saída da CLI (`O padr�o � sempre test`)

- **Sintoma:** `uv run seed --help` mostrou `padr�o` em vez de `padrão` quando a saída foi redirecionada (pipe ou arquivo).
- **Causa:** no Windows, quando a saída não é um console interativo, o Python usa a codificação local (`cp1252`), e quem lê espera UTF-8. No terminal do PowerShell/Cursor, o Python escreve direto no console e os acentos aparecem certos.
- **Solução:** ativar o modo UTF-8 do Python com a variável `PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8 = "1"`; para ficar permanente: `setx PYTHONUTF8 1`).
