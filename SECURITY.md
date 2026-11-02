# Política de Segurança

Este repositório guarda o schema PostgreSQL do Quimia e a ferramenta de carga (`seed`) que popula os bancos no Aiven. Ele **não contém credenciais**, e queremos que continue assim.

## Versões com suporte

Só a versão mais recente da branch `main` recebe correções de segurança.

## Como reportar uma vulnerabilidade

**Não abra uma issue pública** para problemas de segurança.

1. Abra a aba **Security** do repositório e use **Report a vulnerability** (relato privado de vulnerabilidade do GitHub).
2. Descreva o que encontrou, como reproduzir e qual o impacto. Não inclua senhas ou dados reais no relato.

Se a opção não estiver disponível, entre em contato com os mantenedores da organização Quimia-br pelo GitHub, sem detalhes técnicos em canal público.

Você receberá uma confirmação em até **5 dias úteis** e atualizações sobre a correção conforme ela avançar.

## O que consideramos relevante

- Credenciais, tokens, certificados ou `.env` versionados por engano.
- Formas de contornar as travas do banco principal (`reset`, `--allow-synthetic`, confirmações).
- Falhas que permitam executar os scripts de `database/sql/` (que apagam tabelas) sem querer.
- Dependências com vulnerabilidade conhecida que afetem o projeto.

## Se uma credencial vazar

1. **Troque a senha e o certificado imediatamente** no console do Aiven. Apagar o commit não basta: o valor fica no histórico e em caches.
2. Avise os mantenedores.
3. Só depois limpe o histórico, se necessário.

## Boas práticas já adotadas

- `.env`, `.env.test` e `certs/` ficam fora do Git.
- O hook `detect-private-key` do pre-commit bloqueia chaves privadas.
- O `seed` usa SSL com validação do certificado e dados sintéticos em domínios reservados (`example.com` e `example.org`).
- Nenhuma automação executa comandos contra o banco principal.
