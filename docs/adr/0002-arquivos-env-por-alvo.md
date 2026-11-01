# ADR 0002: Um arquivo de configuração por alvo

Status: Aceita

## Contexto

Cada alvo (`test` e `main`) tem host, porta, usuário, senha e certificado próprios. O arquivo `.env` é carregado automaticamente por várias ferramentas, o que aumenta o risco de usar as credenciais do banco principal sem querer.

## Decisão

Usar `.env.test` para o banco de teste e **`.env` para o principal**, os dois fora do Git. Como proteção extra:

- o `.vscode/settings.json` não injeta o `.env` no editor;
- o alvo `test` aborta se resolver para o mesmo host e porta do `.env`.

## Consequências

- Credenciais do `main` nunca são carregadas por engano ao trabalhar no `test`.
- Quem configura o projeto precisa preencher dois arquivos (ver o README).
