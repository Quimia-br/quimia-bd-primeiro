# ADR 0007: Modelos ORM só para descrever tabelas e contratos Pydantic para validar linhas

Status: Aceita

## Contexto

Sem Alembic ([ADR 0006](0006-sql-fonte-da-verdade-sem-alembic.md)), o projeto poderia dispensar também os modelos ORM e a validação em Python. Mas é preciso saber a ordem de carga das tabelas, ter tipagem e detectar divergências com o banco real, além de pegar dados inválidos antes de chegar ao banco.

## Decisão

- **Modelos ORM (SQLAlchemy 2.0)** só descrevem as tabelas e não as criam. Dão a ordem de carga (`metadata.sorted_tables`), a tipagem e a base da comparação com o banco real feita pelo `seed check`.
- **Inserts pelo Core:** `insert(Modelo.__table__)` com lista de dicionários e `RETURNING`, nunca `session.add` linha a linha.
- **Contratos Pydantic** validam cada linha antes do insert: tamanhos, valores dos CHECKs, CAS, CNPJ, CEP, e-mail, URL e datas.

## Consequências

- Um erro de dado aparece com o nome do campo, antes de chegar ao banco.
- Há três representações do schema para manter em sincronia ([ADR 0008](0008-mudanca-de-schema-em-tres-lugares.md)).
