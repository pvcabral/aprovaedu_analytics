-- Análise extra: aprovação por modelo de ensino do aluno, em cada ano.
--
-- Dois grupos e não três porque só existem duas combinações na base: aluno que fez
-- tudo online, e aluno que fez presencial e híbrido ao mesmo tempo. Isso vem da
-- estrutura das unidades, já que as unidades físicas oferecem as duas modalidades
-- lado a lado, então separar presencial de híbrido por aluno é impossível aqui.
WITH modalidades_do_aluno AS (
    SELECT
        m.aluno_id,
        m.ano,
        COUNT(DISTINCT o.modalidade) AS modalidades,
        MIN(o.modalidade)            AS unica_modalidade
    FROM matriculas m
    JOIN ofertas_curso o ON o.oferta_id = m.oferta_id
    WHERE m.ano IS NOT NULL
      AND o.modalidade IS NOT NULL
    GROUP BY m.aluno_id, m.ano
),
grupo AS (
    SELECT
        aluno_id,
        ano,
        CASE
            WHEN modalidades = 1 AND unica_modalidade = 'Online' THEN 'Só online'
            ELSE 'Presencial e híbrido'
        END AS modelo_de_ensino
    FROM modalidades_do_aluno
),
aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
)
SELECT
    g.modelo_de_ensino,
    g.ano,
    COUNT(*)                                       AS alunos,
    COUNT(a.aluno_id)                              AS aprovados,
    ROUND(100.0 * COUNT(a.aluno_id) / COUNT(*), 1) AS taxa_aprovacao
FROM grupo g
LEFT JOIN aprovado_no_ano a
    ON  a.aluno_id       = g.aluno_id
    AND a.ano_vestibular = g.ano
GROUP BY g.modelo_de_ensino, g.ano
ORDER BY g.modelo_de_ensino, g.ano;
