# 0017. SSL verify-ca em vez de verify-full, por limitação do libpq no Windows

- **Status:** aceita (altera o modo SSL da [ADR 0001](0001-sem-docker-aiven-dois-servicos.md))
- **Data:** 2026-10-03

## Contexto

Com `sslmode=verify-full`, o primeiro `seed check` falhou com `certificate contains IP address with invalid length 16`. O certificado dos servidores do Aiven lista, além do nome do host, os endereços IP do servidor, incluindo um IPv6 (16 bytes). O libpq embutido no `psycopg-binary` 3.3.6 para Windows (libpq 18.4) rejeita essa entrada ao conferir o nome do host, em vez de ignorá-la. A senha, a porta, a allowlist e o CA estavam corretos.

## Decisão

- O padrão de `SEED_DB_SSLMODE` passa a ser **`verify-ca`**: a conexão continua criptografada e o certificado do servidor continua sendo validado contra o CA do projeto no Aiven (`SEED_DB_SSLROOTCERT`). Só a conferência do nome do host deixa de ser feita.
- `verify-full` continua aceito na configuração, para quando o driver for corrigido ou em outro sistema operacional.
- Modos que não validam o certificado (`require`, `prefer`, `disable`) continuam recusados.
- O `seed check` passa a dar uma dica específica por tipo de erro de conexão (SSL, senha, banco, host, rede), em vez de sempre citar a allowlist.

## Alternativas descartadas

- **Compilar o psycopg com `psycopg[c]` contra outro libpq:** no Windows exige o PostgreSQL e o compilador do Visual Studio instalados, sem garantia de resolver.
- **Testar outras versões do `psycopg-binary`:** tentativa e erro, e a próxima atualização poderia trazer o problema de volta.
- **`sslmode=require`:** criptografa, mas não valida o certificado.

## Consequências

- Risco residual baixo: cada projeto do Aiven tem um CA próprio, então só um servidor do mesmo projeto teria um certificado aceito no lugar do esperado.
- Vale reavaliar quando uma nova versão do `psycopg-binary` trouxer outro libpq: basta testar `SEED_DB_SSLMODE=verify-full` no `.env.test`.
