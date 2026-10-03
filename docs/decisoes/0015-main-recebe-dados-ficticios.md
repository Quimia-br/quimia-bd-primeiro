# 0015. O main recebe dados fictícios, exceto auditoria, com --allow-synthetic

- **Status:** aceita (substitui a [ADR 0013](0013-main-sem-dados-sinteticos.md))
- **Data:** 2026-10-03

## Contexto

A ADR 0013 previa que o banco principal recebesse só dados de referência e o catálogo revisado. O Nicolas decidiu que o `main` também precisa de dados fictícios (usuários, empresas, estantes, históricos etc.), por exemplo para usar e apresentar o app.

## Decisão

- O `main` pode receber dados fictícios em **todas as tabelas, exceto `admin_log_edicoes`**, que continua sem dados fictícios no `main` ([ADR 0008](0008-admin-log-somente-no-test.md)): auditoria falsa é pior que auditoria vazia.
- A carga fictícia no `main` exige a opção **`--allow-synthetic`** e uma confirmação digitando o nome do banco. Sem a opção, o `main` recebe só referência e catálogo revisado.
- Continuam proibidos no `main`, garantido pelo código: `seed reset`, o perfil `perf` e qualquer `TRUNCATE`/`DELETE`.
- Os textos de segurança (descarte, precaução, restrição) continuam vindo só de entradas do catálogo com `revisado: true`.
- `SEED_PASSWORD_PLAIN` passa a ser aceita no arquivo do `main` (o `.env`, [ADR 0016](0016-env-e-o-arquivo-do-principal.md)), com uma senha **diferente** da do `.env.test`. Se a senha de teste vazar, ela não dá acesso às contas fictícias do `main`.
- O assistente continua sem executar nada contra o `main`: ele prepara o comando e o Nicolas executa.

## Alternativas descartadas

- **Só contas fictícias no main:** o app ficaria sem estantes e históricos para demonstrar.
- **Incluir a auditoria:** registros de auditoria inventados no banco principal confundiriam qualquer investigação real.
- **Carga fictícia sem opção extra:** um `seed run --target main` por engano carregaria dados fictícios.
- **Mesma senha nos dois bancos:** um vazamento no `test` exporia o `main`.

## Consequências

- Dados fictícios e dados reais podem conviver no `main`. Os e-mails fictícios usam `example.com` e `example.org`, o que permite identificá-los e, se preciso, removê-los manualmente (o seed nunca apaga no `main`).
- Os testes da CLI (Fase 8) provam que, no `main`, a carga fictícia exige `--allow-synthetic` e a confirmação, e que `admin_log_edicoes` nunca é carregada.
