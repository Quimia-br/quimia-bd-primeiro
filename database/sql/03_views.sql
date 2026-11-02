DROP MATERIALIZED VIEW IF EXISTS mv_dashboard;
 
CREATE OR REPLACE VIEW vw_dashboard_alertas AS
SELECT CONCAT(nome, ' Usuário (', status, ')') AS alerta
FROM usuarios
WHERE status IN ('BLOQUEADO', 'PENDENTE')
UNION ALL
SELECT CONCAT(nome, ' Empresa (', status, ')')
FROM usuarios_empresas
WHERE status IN ('BLOQUEADO', 'PENDENTE')
UNION ALL
SELECT CONCAT(nome, ' Administrador (', status, ')')
FROM admins
WHERE status IN ('BLOQUEADO', 'PENDENTE');
 
CREATE OR REPLACE VIEW vw_dashboard_totais AS
SELECT (SELECT COUNT(*) FROM usuarios)                    AS contagem_usuarios,
       (SELECT COUNT(*) FROM produtos)                    AS contagem_produtos,
       (SELECT COUNT(*) FROM usuarios_empresas)           AS contagem_empresas,
       (SELECT COUNT(*) FROM vw_dashboard_alertas) AS contagem_alertas;
 
CREATE OR REPLACE VIEW vw_dashboard_atividade_admin AS
SELECT a.nome AS admin,
       ale.acao,
       ale.data_edicao,
       ale.tabela_afetada
FROM admin_log_edicoes ale
         JOIN admins a ON a.id_admin = ale.id_admin
ORDER BY ale.data_edicao DESC
LIMIT 20;
 
CREATE OR REPLACE VIEW vw_dashboard_produtos_mais_usados AS
SELECT p.nome   AS nome_produto,
       COUNT(*) AS total_usos
FROM produtos p
         JOIN (SELECT id_produto FROM produtos_usuarios
               UNION ALL
               SELECT id_produto FROM produtos_estantes
               UNION ALL
               SELECT id_produto FROM historicos_produtos) uso
              ON uso.id_produto = p.id_produto
GROUP BY p.id_produto, p.nome;
 
CREATE OR REPLACE VIEW vw_dashboard_tipos_consulta AS
SELECT th.nome  AS nome_tipo,
       COUNT(*) AS tipo_contagem
FROM historicos h
         JOIN tipos_historicos th ON th.id_tipo_historico = h.id_tipo_historico
GROUP BY th.id_tipo_historico, th.nome;
 
CREATE OR REPLACE VIEW vw_dashboard_atividade_uso AS
SELECT u.nome                           AS usuario,
       th.nome                          AS tipo,
       CAST(h.data_execucao AS TIMESTAMP) AS data_execucao
FROM historicos h
         JOIN usuarios u          ON u.id_usuario = h.id_usuario
         JOIN tipos_historicos th ON th.id_tipo_historico = h.id_tipo_historico
ORDER BY h.data_execucao DESC
LIMIT 20;
 
CREATE OR REPLACE VIEW vw_dashboard_atividade_por_dia AS
SELECT CAST(data_edicao AS DATE) AS dia, COUNT(*) AS total
FROM admin_log_edicoes
WHERE data_edicao >= CURRENT_DATE - 89
GROUP BY 1;

CREATE OR REPLACE VIEW vw_dashboard_uso_por_dia AS
SELECT CAST(data_execucao AS DATE) AS dia, COUNT(*) AS total
FROM historicos
WHERE data_execucao >= CURRENT_DATE - 179
GROUP BY 1;

CREATE OR REPLACE VIEW vw_dashboard_usuarios_por_dia AS
SELECT CAST(data_cadastro AS DATE) AS dia, COUNT(*) AS total
FROM usuarios
WHERE data_cadastro >= CURRENT_DATE - 179
GROUP BY 1;
 
CREATE OR REPLACE VIEW vw_dashboard_empresas_por_dia AS
SELECT CAST(data_cadastro AS DATE) AS dia, COUNT(*) AS total
FROM usuarios_empresas
WHERE data_cadastro >= CURRENT_DATE - 179
GROUP BY 1;

CREATE OR REPLACE VIEW vw_dashboard_usuarios_por_mes AS
SELECT CAST(date_trunc('month', data_cadastro) AS DATE) AS dia, COUNT(*) AS total
FROM usuarios
WHERE data_cadastro >= date_trunc('month', LOCALTIMESTAMP) - INTERVAL '5 months'
GROUP BY 1;

CREATE OR REPLACE VIEW vw_dashboard_empresas_por_mes AS
SELECT CAST(date_trunc('month', data_cadastro) AS DATE) AS dia, COUNT(*) AS total
FROM usuarios_empresas
WHERE data_cadastro >= date_trunc('month', LOCALTIMESTAMP) - INTERVAL '5 months'
GROUP BY 1;
 
CREATE OR REPLACE VIEW vw_dashboard_series AS
SELECT 6  AS ordem, 'atividade_dia'::TEXT        AS secao, dia, total FROM vw_dashboard_atividade_por_dia
UNION ALL
SELECT 7,           'uso_dia'::TEXT,                       dia, total FROM vw_dashboard_uso_por_dia
UNION ALL
SELECT 8,           'cadastro_usuario_dia'::TEXT,          dia, total FROM vw_dashboard_usuarios_por_dia
UNION ALL
SELECT 9,           'cadastro_empresa_dia'::TEXT,          dia, total FROM vw_dashboard_empresas_por_dia
UNION ALL
SELECT 10,          'cadastro_usuario_mes'::TEXT,          dia, total FROM vw_dashboard_usuarios_por_mes
UNION ALL
SELECT 11,          'cadastro_empresa_mes'::TEXT,          dia, total FROM vw_dashboard_empresas_por_mes;
 
 
-- ===================================
--  MATERIALIZED VIEW AGREGADORA
-- ===================================

CREATE MATERIALIZED VIEW mv_dashboard AS
WITH secoes AS (
    -- 1. totais
    SELECT 1 AS ordem, 'totais'::TEXT AS secao,
           contagem_usuarios, contagem_produtos, contagem_empresas, contagem_alertas,
           NULL::TEXT AS admin, NULL::TEXT AS acao,
           NULL::TIMESTAMP WITHOUT TIME ZONE AS data_edicao, NULL::TEXT AS tabela_afetada,
           NULL::TEXT AS alerta,
           NULL::BIGINT AS total_usos, NULL::TEXT AS nome_produto,
           NULL::BIGINT AS tipo_contagem, NULL::TEXT AS nome_tipo,
           NULL::DATE AS data_dia, NULL::BIGINT AS total_dia
    FROM vw_dashboard_totais
 
    UNION ALL
    SELECT 2, 'alerta',
           NULL, NULL, NULL, NULL,
           NULL, NULL, NULL, NULL,
           alerta,
           NULL, NULL, NULL, NULL, NULL, NULL
    FROM vw_dashboard_alertas
 
    UNION ALL
    SELECT 3, 'atividade',
           NULL, NULL, NULL, NULL,
           admin, acao, data_edicao, tabela_afetada,
           NULL,
           NULL, NULL, NULL, NULL, NULL, NULL
    FROM vw_dashboard_atividade_admin
 
    UNION ALL
    SELECT 4, 'produto',
           NULL, NULL, NULL, NULL,
           NULL, NULL, NULL, NULL,
           NULL,
           total_usos, nome_produto, NULL, NULL, NULL, NULL
    FROM vw_dashboard_produtos_mais_usados
 
    UNION ALL
    SELECT 5, 'tipo_consulta',
           NULL, NULL, NULL, NULL,
           NULL, NULL, NULL, NULL,
           NULL,
           NULL, NULL, tipo_contagem, nome_tipo, NULL, NULL
    FROM vw_dashboard_tipos_consulta
 
    UNION ALL 
    SELECT ordem, secao,
           NULL, NULL, NULL, NULL,
           NULL, NULL, NULL, NULL,
           NULL,
           NULL, NULL, NULL, NULL, dia, total
    FROM vw_dashboard_series
 
    UNION ALL 
    SELECT 12, 'atividade_uso',
           NULL, NULL, NULL, NULL,
           usuario, NULL, data_execucao, NULL,
           NULL,
           NULL, NULL, NULL, tipo, NULL, NULL
    FROM vw_dashboard_atividade_uso
)
SELECT ROW_NUMBER() OVER (ORDER BY ordem,
                                   data_edicao   DESC NULLS LAST,
                                   total_usos    DESC NULLS LAST,
                                   tipo_contagem DESC NULLS LAST,
                                   data_dia,
                                   alerta) AS id,
       NOW() AS atualizado_em,
       secoes.*
FROM secoes;
 
 
-- =========================
--  OWNER E INDÍCES
-- =========================

ALTER VIEW vw_dashboard_alertas              OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_totais               OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_atividade_admin      OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_produtos_mais_usados OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_tipos_consulta       OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_atividade_uso        OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_atividade_por_dia    OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_uso_por_dia          OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_usuarios_por_dia     OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_empresas_por_dia     OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_usuarios_por_mes     OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_empresas_por_mes     OWNER TO quimiawebcrud;
ALTER VIEW vw_dashboard_series               OWNER TO quimiawebcrud;
ALTER MATERIALIZED VIEW mv_dashboard         OWNER TO quimiawebcrud;
 
CREATE UNIQUE INDEX mv_dashboard_id_idx    ON mv_dashboard (id);
CREATE INDEX        mv_dashboard_secao_idx ON mv_dashboard (secao);

-- =================================
-- MUDANÇA DE OWNER
-- =================================

ALTER MATERIALIZED VIEW mv_dashboard OWNER TO quimiawebcrud;
 