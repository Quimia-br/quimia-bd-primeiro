# 0016. O .env é o arquivo do banco principal, com proteções contra injeção automática

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

O seed lia `.env.test` para o alvo `test` e `.env.main` para o `main`. O Nicolas já usa o `.env` comum para o banco principal e decidiu mantê-lo. O `.env` é carregado automaticamente por várias ferramentas, por exemplo a extensão Python do Cursor/VS Code (configuração `python.envFile`), que injeta o conteúdo como variáveis de ambiente nos testes, no debugger e às vezes no terminal. Como as variáveis de ambiente têm prioridade sobre o arquivo do alvo, um comando com alvo `test` poderia conectar no banco principal sem aviso.

## Decisão

- O alvo `main` lê o **`.env`**. O alvo `test` continua lendo o `.env.test`.
- **Proteção no editor:** `.vscode/settings.json` aponta `python.envFile` para um arquivo inexistente e desliga `python.terminal.useEnvFile`, para nada ser injetado automaticamente.
- **Proteção no código:** ao carregar o alvo `test`, se o host e a porta resolvidos forem iguais aos `SEED_DB_HOST` e `SEED_DB_PORT` do `.env`, o seed aborta com erro de configuração. Isso pega tanto a injeção pelo ambiente quanto um `.env.test` preenchido por engano com os dados do principal.

## Alternativas descartadas

- **Renomear o `.env` para `.env.main`:** recomendado inicialmente, por não depender de proteções extras; o Nicolas preferiu manter o `.env`.

## Consequências

- A segurança do alvo `test` depende das duas proteções. Em outra máquina, o `.vscode/settings.json` vem pelo Git; a trava do código vale em qualquer lugar.
- Se outra ferramenta carregar o `.env` no ambiente, os comandos com alvo `test` passam a falhar com uma mensagem clara, em vez de conectar no principal.
- As regras de não ler o `.env` continuam valendo para o assistente (`.claude/settings.local.json` e `CLAUDE.md`).
