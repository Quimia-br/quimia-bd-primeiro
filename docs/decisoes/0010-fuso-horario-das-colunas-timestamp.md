# 0010. Fuso horário das colunas TIMESTAMP sem fuso

- **Status:** aceita
- **Data:** 2026-10-03

## Contexto

Todas as colunas de data do DDL são `TIMESTAMP` sem fuso, com `DEFAULT CURRENT_TIMESTAMP`, que grava no **fuso da sessão**. Se o seed gravar num fuso e o backend em outro, registros criados no mesmo instante ficam com horas de diferença. Serviços gerenciados como o Aiven costumam vir em UTC.

## Decisão

- O seed **não usa um fuso fixo**. O fuso de gravação é `SEED_TIMEZONE`, com padrão `UTC`.
- O `seed check` mostra o resultado de `SHOW timezone` e avisa em amarelo se ele for diferente de `SEED_TIMEZONE`.
- O `seed run` se recusa a rodar com essa divergência, a menos que uma opção explícita seja passada.
- As datas são geradas *aware* (com fuso) em `America/Sao_Paulo`, para fazerem sentido como horário de uso no Brasil. Depois são convertidas para `SEED_TIMEZONE` e só então gravadas sem fuso.
- Os cálculos de idade e de ordem entre datas são feitos antes da conversão, sobre os valores com fuso.

## Alternativas descartadas

- **Gravar sempre em São Paulo:** ficaria diferente do `DEFAULT CURRENT_TIMESTAMP` se o servidor estiver em UTC.
- **Gravar sempre em UTC, sem verificação:** quebraria se o backend usar outro fuso.
- **Migrar para TIMESTAMPTZ:** resolveria o problema, mas é mudança de schema ([ADR 0005](0005-nenhuma-melhoria-de-schema-agora.md)); está na [pauta, item 6](../pauta-reuniao.md).

## Consequências

- Os registros do seed ficam no mesmo fuso que o servidor usa nos defaults.
- Continua pendente saber se o backend configura o fuso da sessão (pauta, item 6).
