# ADR 0023: Como produtos, estantes e históricos são distribuídos

Status: Aceita

## Contexto

Os históricos de MISTURA exigem de 2 a 4 produtos do mesmo usuário, e as regras por tipo ([ADR 0016](0016-tipos-de-historico-e-regras-por-tipo.md)) limitam quantos produtos cada histórico pode ter.

## Decisão

- **Produtos concentrados em parte dos usuários:** 100 posses para 100 usuários não permitiriam misturas. Por isso entre 25 e 37 usuários têm de 2 a 4 produtos cada, e os outros não têm nenhum (nem históricos com produtos).
- **Estantes:** todo dono de produto tem de 1 a 3 estantes, e as restantes vão para outros usuários (vazias). Cada produto possuído fica em exatamente uma estante do dono, então `produtos_estantes` tem uma linha por posse.
- **Históricos:** primeiro é planejado o tipo e o número de produtos de cada um, para somarem exatamente 100 em `historicos_produtos` respeitando o mínimo e o máximo de cada tipo. Nos tipos com estante obrigatória (ARMAZENAMENTO e VERIFICACAO), os produtos são os guardados naquela estante, com `data_adicao` até a data do histórico. Nos outros, são produtos do usuário.

## Consequências

- Se as regras não permitirem as quantidades pedidas, o seed para com um erro em vez de quebrar uma regra.
- Testado com 300 sementes diferentes, sem falha.
