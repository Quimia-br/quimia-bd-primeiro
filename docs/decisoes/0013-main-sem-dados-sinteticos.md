# 0013. O main recebe só referência e catálogo revisado

- **Status:** substituída pela [ADR 0015](0015-main-recebe-dados-ficticios.md)
- **Data:** 2026-10-03

## Contexto

O banco principal guarda dados reais do app. Dados sintéticos misturados a eles confundiriam relatórios e usuários.

## Decisão

- No `main`, o seed carrega apenas dados de referência e entradas do catálogo marcadas com `revisado: true` por uma pessoa.
- Sem `--allow-synthetic`, nenhum dado sintético é aceito. A opção existe no código, com dupla confirmação, mas a política do projeto é não usá-la.
- `admin_log_edicoes` nunca recebe dados sintéticos no `main`, nem com a opção ([ADR 0008](0008-admin-log-somente-no-test.md)).
- Nada é executado pelo assistente contra o `main`: ele só prepara comandos e SQL, e o Nicolas executa.

## Alternativas descartadas

- **Permitir dados sintéticos de demonstração no main:** risco de misturar dados falsos com reais.

## Consequências

- No `main`, a carga é aditiva com `ON CONFLICT DO NOTHING` nas chaves naturais, sem `TRUNCATE` nem `DELETE`.
