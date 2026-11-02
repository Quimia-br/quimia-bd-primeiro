# ADR 0013: E-mails sintéticos só em domínios reservados

Status: Aceita

## Contexto

Os dados gerados nunca devem coincidir com pessoas reais nem causar envio de e-mail a terceiros.

## Decisão

Gerar e-mails só com os domínios reservados `example.com` e `example.org` (lista em `config.py`), em minúsculas.

## Consequências

- Nenhum e-mail sintético pertence a uma pessoa real.
