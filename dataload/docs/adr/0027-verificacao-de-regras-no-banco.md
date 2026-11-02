# ADR 0027: `seed verificar` confere as regras de negócio no banco

Status: Aceita

## Contexto

Os contratos validam as linhas antes do insert, mas não garantem que o conjunto gravado no banco respeite as regras entre tabelas.

## Decisão

O comando `seed verificar` consulta o banco (somente leitura) e mostra aprovada ou reprovada por regra. Regras conferidas: estante e produtos do mesmo usuário, regras por tipo de histórico, um descarte por produto, datas, idade mínima, uma estante por cômodo, logs coerentes, e-mails, CNPJ e CAS.

## Consequências

- Uma regra reprovada faz o comando terminar com código de saída 8.
