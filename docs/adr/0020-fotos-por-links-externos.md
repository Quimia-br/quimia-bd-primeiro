# ADR 0020: Fotos por links externos

Status: Aceita

## Contexto

Usuários e empresas têm URL de foto. Hospedar imagens próprias aumentaria o escopo do projeto.

## Decisão

- Usuários: `https://randomuser.me/api/portraits/{men|women}/{0-99}.jpg`, com o gênero da foto combinando com o nome e sem repetir índice.
- Empresas: `https://ui-avatars.com/api/?name=<nome>&size=256`.
- Os formatos ficam em `config.py`.
- Os índices 0 a 99 do randomuser.me (pastas `women` e `men`) e o formato do ui-avatars foram conferidos em 04/10/2026.

## Consequências

- **Risco:** são links externos; se um serviço mudar ou sair do ar, as imagens quebram. Hospedar as imagens é uma alternativa em aberto.
