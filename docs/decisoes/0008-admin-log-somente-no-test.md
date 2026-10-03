# 0008. admin_log_edicoes populada só no test, com regras por ação

- **Status:** aceita (quem escreve no app está pendente; ver [pauta, item 12](../pauta-reuniao.md))
- **Data:** 2026-10-03

## Contexto

`admin_log_edicoes` registra edições feitas por admins. Ainda não se sabe se o app a escreve pelo backend ou por trigger. Dados de auditoria falsos no banco principal seriam enganosos.

## Decisão

- O seed popula a tabela **só no alvo `test`**: dev ~30, demo ~10, perf ~5.000 registros.
- **No `main`, a tabela nunca recebe dados sintéticos, nem com `--allow-synthetic`**, porque auditoria falsa é pior que auditoria vazia. Isso é garantido no código e provado nos testes da CLI.
- As tabelas auditáveis ficam em YAML em `data/reference/` (provisório: `usuarios`, `usuarios_empresas`, `produtos`, `descartes_fds`, `tipos_historicos`).
- Regras por ação:
  - **INSERT:** `id_registro` existe e `dado_anterior` é nulo. Nas tabelas com `data_cadastro`, `data_edicao` coincide com ela; nas outras, fica entre o cadastro do admin e o momento da carga.
  - **UPDATE:** `id_registro` existe e `dado_anterior` é o JSON da linha com os valores antigos, diferindo do atual em pelo menos um campo.
  - **DELETE:** `id_registro` não existe mais na tabela, e `dado_anterior` traz a linha completa apagada. Para isso, a linha é inserida e apagada na mesma transação: o ID é consumido pela identity e nunca será reutilizado.
  - Em todos os casos, `data_edicao` é posterior ao `data_cadastro` do admin.
- `dado_anterior` é gravado com `json.dumps(..., ensure_ascii=False)`.

## Alternativas descartadas

- **Não popular a tabela:** as telas de auditoria ficariam sem dados de teste.
- **DELETE com um ID inventado acima do máximo:** a identity poderia gerar esse mesmo ID depois, e o log apontaria para um registro novo e sem relação.

## Consequências

- A antiga regra "`id_registro` sempre existe" foi corrigida: não vale para DELETE.
- Se o app passar a usar trigger, o seed precisa ser revisto (pauta, item 12).
