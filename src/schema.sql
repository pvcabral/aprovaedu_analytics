-- Schema do banco "desafio_logap"
-- Ordem de criação respeita as dependências de FK.
-- Ordem de DROP é a reversa, para permitir rodar o script várias vezes (idempotente).

DROP TABLE IF EXISTS presencas_aulas CASCADE;
DROP TABLE IF EXISTS aulas CASCADE;
DROP TABLE IF EXISTS resultados_sim CASCADE;
DROP TABLE IF EXISTS simulados CASCADE;
DROP TABLE IF EXISTS aprovacoes CASCADE;
DROP TABLE IF EXISTS matriculas CASCADE;
DROP TABLE IF EXISTS ofertas_curso CASCADE;
DROP TABLE IF EXISTS estudantes CASCADE;
DROP TABLE IF EXISTS professor_materia CASCADE;
DROP TABLE IF EXISTS professores CASCADE;
DROP TABLE IF EXISTS dim_materia CASCADE;

-- Dimensão de matérias, criada a partir de amostra_professores no tratamento
CREATE TABLE dim_materia (
    materia_id      INTEGER PRIMARY KEY,
    nome_materia    TEXT NOT NULL UNIQUE
);

CREATE TABLE professores (
    professor_id            TEXT PRIMARY KEY,
    nome_professor          TEXT NOT NULL,
    email_professor         TEXT,
    materia_id              INTEGER REFERENCES dim_materia(materia_id),
    data_contratacao        DATE,
    status_professor        TEXT,
    unidade_base            TEXT,
    carga_horaria_semanal   NUMERIC,
    observacoes             TEXT
);

-- Relacionamento N:N professor <-> matéria (um professor pode ensinar mais de uma matéria)
CREATE TABLE professor_materia (
    professor_id    TEXT NOT NULL REFERENCES professores(professor_id),
    materia_id      INTEGER NOT NULL REFERENCES dim_materia(materia_id),
    PRIMARY KEY (professor_id, materia_id)
);

CREATE TABLE estudantes (
    aluno_id         TEXT PRIMARY KEY,
    nome_aluno       TEXT NOT NULL,
    cpf_ficticio     TEXT,
    email_aluno      TEXT,
    telefone         TEXT,
    data_nascimento  DATE,
    cidade           TEXT,
    escola_origem    TEXT,
    data_cadastro    DATE,
    canal_captacao   TEXT
);

CREATE TABLE ofertas_curso (
    oferta_id             TEXT PRIMARY KEY,
    ano                   INTEGER,
    turma                 TEXT,
    turno                 TEXT,
    unidade               TEXT,
    materia_id            INTEGER REFERENCES dim_materia(materia_id),
    professor_id          TEXT REFERENCES professores(professor_id),
    modalidade            TEXT,
    carga_horaria_total   INTEGER,
    preco_lista           NUMERIC,
    data_inicio           DATE,
    data_fim              DATE
);

CREATE TABLE matriculas (
    matricula_id        TEXT PRIMARY KEY,
    aluno_id             TEXT REFERENCES estudantes(aluno_id),
    oferta_id            TEXT REFERENCES ofertas_curso(oferta_id),
    ano                  INTEGER,
    materia_id           INTEGER REFERENCES dim_materia(materia_id),
    data_matricula       DATE,
    bolsa_percentual     NUMERIC,
    status_matricula     TEXT,
    nota_diagnostico     NUMERIC,
    origem_captacao      TEXT
);

CREATE TABLE aprovacoes (
    aprovacao_id            TEXT PRIMARY KEY,
    ano_vestibular          INTEGER,
    aluno_id                TEXT REFERENCES estudantes(aluno_id),
    universidade             TEXT,
    curso_aprovado           TEXT,
    modalidade_vaga          TEXT,
    chamada                  TEXT,
    bolsa_aprovacao          TEXT,
    data_resultado           DATE,
    nota_final_vestibular    NUMERIC,
    campus                   TEXT
);

CREATE TABLE simulados (
    simulado_id         TEXT PRIMARY KEY,
    ano                 INTEGER,
    data_simulado        DATE,
    materia_id           INTEGER REFERENCES dim_materia(materia_id),
    professor_id         TEXT REFERENCES professores(professor_id),
    dificuldade          TEXT,
    tipo_simulado        TEXT,
    total_questoes       INTEGER,
    tempo_limite_min     INTEGER,
    tema                 TEXT
);

CREATE TABLE resultados_sim (
    resultado_id             TEXT PRIMARY KEY,
    simulado_id              TEXT REFERENCES simulados(simulado_id),
    aluno_id                 TEXT REFERENCES estudantes(aluno_id),
    ano                      INTEGER,
    status_realizacao        TEXT,
    nota                     NUMERIC,
    acertos                  NUMERIC,
    tempo_finalizacao_min    NUMERIC,
    inicio_simulado          TIMESTAMP,
    dispositivo              TEXT,
    tentativas               NUMERIC,
    unidade_aplicacao        TEXT,
    nota_acima_lim           BOOLEAN,
    tempo_acima_lim          BOOLEAN
);

CREATE TABLE aulas (
    aula_id           TEXT PRIMARY KEY,
    oferta_id         TEXT REFERENCES ofertas_curso(oferta_id),
    ano               INTEGER,
    data_aula         DATE,
    materia_id        INTEGER REFERENCES dim_materia(materia_id),
    professor_id      TEXT REFERENCES professores(professor_id),
    turma             TEXT,
    tema_aula         TEXT,
    duracao_min       NUMERIC,
    modalidade_aula   TEXT
);

CREATE TABLE presencas_aulas (
    presenca_id        TEXT PRIMARY KEY,
    aula_id            TEXT REFERENCES aulas(aula_id),
    aluno_id           TEXT REFERENCES estudantes(aluno_id),
    status_presenca    TEXT,
    atraso_min         NUMERIC,
    justificativa      TEXT
);