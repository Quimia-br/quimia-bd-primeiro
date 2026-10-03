# 0009. Pool 2 + overflow 1 e perfil perf com ~50 mil linhas

- **Status:** aceita (valores a ajustar com dados reais)
- **Data:** 2026-10-03

## Contexto

A versão do Postgres e o plano de cada serviço no Aiven (limite de conexões e de armazenamento) ainda não são conhecidos. Planos pequenos têm poucas conexões e pouco disco.

## Decisão

- Pool de conexões: `pool_size=2`, `max_overflow=1`, `pool_pre_ping=True`.
- Perfil `perf` com cerca de **50 mil linhas no total**, **só no alvo `test`**.
- Pool, overflow e volumes ficam no `.env` e em `config/`, sem mexer no código.
- O `seed check` mostra a versão do Postgres, `max_connections`, as conexões abertas e `pg_database_size`, para ajustar os valores com dados reais.
- Antes de rodar o `perf`, o seed estima o espaço necessário e avisa se estiver perto do limite de armazenamento.

## Alternativas descartadas

- **Pool maior para acelerar:** o seed usa uma transação só, então mais conexões não ajudam e podem esgotar o limite do plano.

## Consequências

- O seed é sequencial; o ganho de desempenho vem dos inserts em lote.
