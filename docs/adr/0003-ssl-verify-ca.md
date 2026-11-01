# ADR 0003: SSL `verify-ca` em vez de `verify-full`

Status: Aceita

## Contexto

O libpq do `psycopg-binary` para Windows rejeita o endereço IPv6 que o Aiven coloca no certificado (`certificate contains IP address with invalid length 16`), o que impede o uso de `verify-full`.

## Decisão

Conectar com `sslmode=verify-ca`.

## Consequências

- A conexão continua criptografada e o certificado continua validado contra o CA do projeto; só o nome do host deixa de ser conferido.
- O risco é baixo, porque cada projeto do Aiven tem um CA próprio.
- Vale testar `verify-full` de novo quando o `psycopg-binary` trouxer outro libpq.
