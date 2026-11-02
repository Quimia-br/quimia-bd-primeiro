# ADR 0026: Recusas antes de gravar

Status: Aceita

## Contexto

Rodar a carga num banco em estado inesperado pode duplicar dados ou gravar datas erradas.

## Decisão

Antes de gravar, o `seed run` recusa a carga quando:

- os modelos divergem do banco;
- o fuso do servidor é diferente de `SEED_TIMEZONE` (a menos que se use `--ignorar-fuso`);
- no `test`, as tabelas não estão vazias (é preciso rodar `seed reset` antes);
- no `main`, algum e-mail, CNPJ ou CAS gerado já existe.

## Consequências

- No `main` a carga só acrescenta: nunca sobrescreve nem apaga.
