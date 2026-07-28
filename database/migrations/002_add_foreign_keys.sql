-- ================================
-- historico --> tipo_historico
-- ================================
ALTER TABLE historico ADD CONSTRAINT fk_historico_tipo_historico
    FOREIGN KEY (id_tipo_historico)
    REFERENCES tipo_historico (id_tipo_historico);

-- ================================
-- historico --> usuario
-- ================================
ALTER TABLE historico ADD CONSTRAINT fk_historico_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario);

-- ================================
-- historico --> estante
-- ================================
ALTER TABLE historico ADD CONSTRAINT fk_historico_estante
    FOREIGN KEY (id_estante)
    REFERENCES estante (id_estante);

-- ================================
-- historico --> produto_superficie
-- ================================
ALTER TABLE historico ADD CONSTRAINT fk_historico_produto_superficie
    FOREIGN KEY (id_produto_superficie)
    REFERENCES produto_superficie (id_produto_superficie);

-- ================================
-- historico --> produto_usuario
-- ================================
ALTER TABLE historico ADD CONSTRAINT fk_historico_produto_usuario
    FOREIGN KEY (id_produto_usuario)
    REFERENCES produto_usuario (id_produto_usuario);

-- ================================
-- produto --> usuario_empresa
-- ================================
ALTER TABLE produto ADD CONSTRAINT fk_produto_usuario_empresa
    FOREIGN KEY (id_usuario_empresa)
    REFERENCES usuario_empresa (id_usuario_empresa);

-- ================================
-- estante --> comodo
-- ================================
ALTER TABLE estante ADD CONSTRAINT fk_estante_comodo
    FOREIGN KEY (id_comodo)
    REFERENCES comodo (id_comodo);

-- ================================
-- estante --> usuario
-- ================================
ALTER TABLE estante ADD CONSTRAINT fk_estante_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario);

-- ================================
-- produto_usuario --> usuario
-- ================================
ALTER TABLE produto_usuario ADD CONSTRAINT fk_produto_usuario_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario);

-- ================================
-- produto_usuario --> produto
-- ================================
ALTER TABLE produto_usuario ADD CONSTRAINT fk_produto_usuario_produto
    FOREIGN KEY (id_produto)
    REFERENCES produto (id_produto);

-- ================================
-- produto_superficie --> produto
-- ================================
ALTER TABLE produto_superficie ADD CONSTRAINT fk_produto_superficie_produto
    FOREIGN KEY (id_produto)
    REFERENCES produto (id_produto);

-- ================================
-- produto_superficie --> superficie
-- ================================
ALTER TABLE produto_superficie ADD CONSTRAINT fk_produto_superficie_superficie
    FOREIGN KEY (id_superficie)
    REFERENCES superficie (id_superficie);

-- ================================
-- localizacao --> usuario
-- ================================
ALTER TABLE localizacao ADD CONSTRAINT fk_localizacao_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario);

-- ================================
-- descarte_fds --> produto
-- ================================
ALTER TABLE descarte_fds ADD CONSTRAINT fk_descarte_fds_produto
    FOREIGN KEY (id_produto)
    REFERENCES produto (id_produto);

-- ================================
-- composto_fds --> produto
-- ================================
ALTER TABLE composto_fds ADD CONSTRAINT fk_composto_fds_produto
    FOREIGN KEY (id_produto)
    REFERENCES produto (id_produto);

-- ================================
-- historico_produto_mistura --> produto
-- ================================
ALTER TABLE historico_produto_mistura ADD CONSTRAINT fk_historico_produto_mistura_produto
    FOREIGN KEY (id_produto)
    REFERENCES produto (id_produto);

-- ================================
-- historico_produto_mistura --> historico
-- ================================
ALTER TABLE historico_produto_mistura ADD CONSTRAINT fk_historico_produto_mistura_historico
    FOREIGN KEY (id_historico)
    REFERENCES historico (id_historico);
