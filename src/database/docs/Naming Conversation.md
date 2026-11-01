INSTITUTO J&F

ANÁLISE E DESENVOLVIMENTO DE SISTEMAS

**QUIMIA**

**DOCUMENTO DE CONVENÇÃO DE NOMENCLATURA E PADRONIZAÇÃO DE NORMAS SQL**

SÃO PAULO

JULHO DE 2026

INSTITUTO J&F

DESENVOLVIMENTO DE SISTEMAS

**QUIMIA**

**DOCUMENTO DE CONVENÇÃO DE NOMENCLATURA E PADRONIZAÇÃO DE NORMAS SQL**

Documento apresentado à disciplina de Banco de Dados como solicitação extra do Projeto Interdisciplinar.

SÃO PAULO

JULHO DE 2026

**SUMÁRIO**

1 INTRODUÇÃO ......................................................................................................... 4

2 DIRETRIZES GERAIS DE ESCRITA ....................................................................... 5

2.1 NORMAS DE ESCRITA PARA ENTIDADES ...........................................5

2.2 NORMAS DE ESCRITA PARA ATRIBUTOS ............................................. 6

3 PADRONIZAÇÃO DE ENTIDADES ......................................................................... 7

4 PADRONIZAÇÃO DE ATRIBUTOS ......................................................................... 9

5 PADRONIZAÇÃO DE CONSTRAINTS ...................................................................10

6 TIPO DE DADO .......................................................................................................11

7 CONCLUSAO ......................................................................................................... 12

**INTRODUÇÃO**

A ausência de padrões na modelagem de dados e a falta de padrões de nomenclatura em bancos de dados frequentemente resulta em inconsistências nos sistemas, ocasionando códigos confusos, vulnerabilidades de segurança e interferindo na manutenção de softwares. Dessa forma, esse documento estabelece um conjunto de normas técnicas e padrões de nomenclatura que são necessários para criação dos objetos presentes no banco de dados relacional, definindo regras de grafia para as tabelas, colunas, restrições e chaves, além de possibilitar uma comunicação mais assertiva entre os desenvolvedores para a elaboração de um software mais seguro e robusto. 

**2** **DIRETRIZES** **GERAIS DE ESCRITA**

Para a padronização geral de grafia de colunas e tabelas, estabelece-se o uso do padrão de convenção: snake_case*.* A sua escolha se deve ao fato da melhora da legibilidade dos códigos, por tratar individualmente cada palavra e por facilitar a leitura de termos compostos, além de evitar erros de compilação do código ao usar o sublinhado como conectivo entre duas palavras substituindo o uso do espaço. Permitindo uma padronização na comunicação do banco de dados relacional com o *backend* **Java. 

Como normas estabelecidas pelo padrão: snake_case, devem ser seguidas obrigatoriamente as seguintes regras de sintaxe ortográfica: 

a) caixa baixa: quaisquer nomes de objetos precisam ser escritos unicamente em letras minúsculas, sendo proibido o uso de letras maiúsculas, por exemplo: “usuarios”, “estantes”; 

b) termos compostos e espaços: quaisquer nomes de objetos que sejam palavras compostas devem ser separados com o uso do sublinhado (_), a mesma regra vale para objetos que por padrão linguístico são separados por espaços ou hifens, por exemplo: “url_foto”, “senha_hash”;

c) uso de caracteres especiais: é proibido o uso de caracteres especiais, pois pode implicar em erros ao compilar o código.

**2.1** **Normas** **de escrita** **para entidades**

As normas estabelecidas para as entidades devem seguir os seguintes padrões de escrita:

a) nomes de entidades: o nome das entidades necessita ser escrito com o uso do plural, por exemplo: “localizacoes”, “produtos”;

b) associativa (N:N): em relacionamentos N:N, as entidades intermediárias precisam ser nomeadas através da junção entre as entidades separadas por sublinhado (_), por exemplo: “produtos_usuarios"; 

c)  associativa entre duas entidades: em relacionamentos que possuem duas entidades, elas precisam ser nomeadas com o uso de plural, por exemplo: "historicos_produtos";

d) enumerativa: entidades do tipo enumerativa precisam seguir a escrita em plural, por exemplo: "tipos_historicos"; 

**2.2 Normas** **de escrita** **para atributos**

As normas estabelecidas para as colunas/atributos seguem os seguintes padrões ortográficos: 

a) chave primária*:* para atributos identificadores os atributos deveram ser escritos utilizando o termo id seguido do nome da tabela no singular, separados pelo uso do sublinhado (_), por exemplo: “id_estante”, “id_usuario”;

b) 	chave estrangeira*:* para chaves estrangeiras os nomes devem seguir exatamente o que está escrito para os atributos identificadores, ou seja, se o nome estiver “id_empresa”, a chave estrangeira deverá se chamar “id_empresa”, respectivamente.

c) 	*constraints* de relacionamento: para *constraints* **que representam um relacionamento, sua nomenclatura deve ser escrita com o prefixo: “fk” e em seguida a tabela de origem e a tabela referenciada, ambas no singular, embora as tabelas estejam no plural, por exemplo: “fk_historico_usuario”, “fk_historico_estante”;

d) 	grafia: os atributos precisam ser escritos no singular, porque um atributo representa uma característica única da entidade, por exemplo: “nome”, “marca”;

e) exceção: atributos que precisam de criptografia e segurança de dados, por exemplo: senhas ou cadastros, devem ser escritas com o prefixo no singular e que seja o atributo e em seguida deve ser escrito como sufixo obrigatório: “hash” que representa a criptografia, por exemplo: “senha_hash”.

**3 PADRONIZAÇÃO DE** **ENTIDADES**

As tabelas compõem a estrutura inicial do banco de dados, abrangendo as entidades e relacionamentos presentes na Modelagem de Dados (ER) e garantindo que os dados e registros associados sejam organizados de forma estruturada. Dessa forma, é fundamental padronizar os nomes das tabelas, a fim de evitar redundâncias no armazenamento de dados, garantir a integridade dos dados e aperfeiçoar a estrutura para que ela seja mais segura e mais veloz. Portanto, como normas estabelecidas as tabelas necessitam seguir os seguintes padrões: 

a)	semântica: É obrigatório em todas as tabelas o uso de substantivos, a fim de evitar ambiguidade no conteúdo. Como padrão não podem ser escritas de maneira longa ou com adjetivos, seguindo de maneira consistente o que os dados devem expressar, por exemplo: “produtos_usuarios”, “localizacoes”;

b) 	entidade de Ficha de Segurança (FDS): é obrigatório em uma entidade de Ficha de Segurança (FDS) o uso do sufixo “*fds”* **no final da palavra para identificar qual o tipo de armazenamento adequado a esse dado, por exemplo*: “*descarte_fds*”;*

c)	entidades com atributos multivalorados: todas as entidades que apresentam atributos multivalorados, devem ser nomeadas com a junção entre a tabela independente com a tabela dependente, por exemplo: “produtos_usuarios”;

d)	tabelas associativas: em entidades associativas/intermediárias o primeiro nome antes do sublinhado (_) é nome da entidade independente, em seguida o nome da entidade dependente, por exemplo: “usuarios_produtos”, “historicos_produtos”.

**4 PADRONIZAÇÃO DE** **ATRIBUTOS**

Os atributos estão presentes dentro da estrutura de uma tabela, determinando qual o tipo de dado armazenado dentro da tabela e definindo qual registro a tabela deve conter. Enquanto as tabelas são a base da estrutura de um banco de dados, os atributos são como um esqueleto que garantem a integridade e o funcionamento adequado das tabelas. Portanto, é de extrema importância o estabelecimento de normas técnicas para garantir a sua integridade e boas práticas de programação, determinados pelos seguintes padrões:

1. atributos temporais: todos os atributos que armazenam datas precisam ser definidos com o tipo: *date* *e* *timestamp* **utilizando o padrão *ISO 8601* que define para datas o padrão (AAAA-MM-DD) e para horas (HH:MM:SS), além disso, sua nomenclatura deve seguir como padrão o prefixo: “data_” e em seguida sufixos que determinam a sua finalidade, por exemplo: “data_nascimento”, “data_execucao”;

1. atributos numéricos: todos os atributos que armazenam valores numéricos devem armazenar valores do tipo: *int* é obrigatório seu uso em atributos identificadores, por exemplo: “id_usuario”, “id_historico”;

1. atributos textuais: todos os atributos que são destinados a valores alfanuméricos devem armazenar valores do tipo: *varchar* **ou *text* **deve **utilizar o padrão de escrita: *UTF-8,* por exemplo, exemplos de atributos textuais do tipo *varchar*: “acao” e “nome” e do tipo *text:* *“*dados_anteriores” e “dosagem_tecnica”;

**5** **PADRONIZAÇÃO DE CONSTRAINTS**

As *constraints* **ou restrições são regras aplicadas em tabelas ou colunas para limitar o tipo de dado presente em um banco de dados conforme a necessidade das regras de negócio. Essas regras são importantes pois garantem a integridade dos dados ao realizar a validação e garantir a confiabilidade dos dados, permitindo um banco de dados relacional mais organizado e com melhor unicidade. Dessa maneira, seguindo o mesmo padrão adotado, deve se seguir a padronização de nomenclatura *snake_case* **e seguindo os padrões descritos:

1. valor único (*unique):* todos os atributos que por regra de negócio não podem ser duplicados ou que são atributos identificadores externos devem utilizar a instrução *unique,* por exemplo: “email”, “cnpj”, “cas_number”;

1. obrigatoriedade (*not* *null):* todos os atributos que por regra de negócio ou que sejam tabelas dependentes obrigatoriamente não podem conter valores nulos em um banco de dados relacional, por exemplo: chaves estrangeiras que por regra de negócio precisam estar vinculado a outra tabela e atributos que devem estar presentes no cadastro do usuário, por exemplo: “email”, *"*cnpj”;

1. validações de regras de negócio (*check*): para atributos que necessitam de verificações lógicas necessitam ser nomeadas seguindo o prefixo: “chk_” e em seguida o sufixo que representa o atributo verificado, a restrição definida ou a junção das duas regras, por exemplo: “chk_porte”, “chk_status”, “chk_url_foto;

1. padronização de valores (default): todas os atributos que necessitam de um valor lógico valores padrões estabelecidos pelas regras de negócio devem utilizar a instrução *default* seguido de valores padrões iniciais, por exemplo: “Sem informação”, “Desconhecido”, “*Current_Timestamp*”.

**6 TIPOS DE** **DADOS**

O estabelecimento de uma padronização no tipo de dados por meio do estabelecimento de número de caracteres padrão conforme o tipo de atributo, favorece a otimização do armazenamento do serviço e melhora a performance ao realizar consultas (*queries*). A seguir estão estabelecidas normas para declaração do tipo de dados:



| **TIPO** | **TAMANHO** | **JUSTIFICATIVA** | **EXEMPLO** |
| :---: | :---: | :---: | :---: |
| VARCHAR | 255 | Descrições longas e textos sem tamanho prévio. | senha_hash |
| VARCHAR | 150 | Atributos que representem valores representativos. | nome, marca |
| VARCHAR | 50 | Atributos curtos e para validação dos dados. | acao, status |
| VARCHAR | Indefinido | Atributos que possuem tamanhos únicos | cnpj, cep |
| TEXT | Indefinido | Descrições longas ou textos que variam de tamanho | dado_anterior, dosagem_tecnica |
| NUMERIC | 9, 6 | Correspondência com os valores de longitude e latitude | longitude, latitude |
**CONCLUSÃO**

Com o desenvolvimento deste trabalho, foi possível consolidar as diretrizes necessárias para garantir a organização, a padronização e a consistência do banco de dados relacional. A definição de regras claras para a criação e a nomeação de tabelas, campos e restrições facilita a leitura do código, evita erros em consultas futuras e simplifica a manutenção da estrutura. Dessa forma, a adoção destas convenções alinha o trabalho da equipe, contribuindo diretamente para a eficiência e a escalabilidade do projeto.


