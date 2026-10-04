"""Geradores de dados sintéticos, um módulo por grupo de tabelas.

Todos usam Faker ``pt_BR`` e ``random.Random`` com a semente única da carga, recebem
os pais já gerados como parâmetro e devolvem linhas validadas pelos contratos
(``seed.contratos``). ``tipos_historicos`` não tem gerador: vem de ``data/reference``.

- ``contas``: usuarios, admins, usuarios_empresas, localizacoes
- ``produtos``: produtos, descartes_fds, produtos_usuarios
- ``estantes``: estantes, produtos_estantes
- ``historicos``: historicos, historicos_produtos, admin_log_edicoes
"""
