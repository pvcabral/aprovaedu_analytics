-- Pergunta 1: evolução da taxa de aprovação ao longo dos anos.
WITH matriculados AS (
    SELECT DISTINCT aluno_id, ano
    FROM matriculas
    WHERE ano IS NOT NULL
      AND aluno_id IS NOT NULL
),
aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
),
por_ano AS (
    SELECT
        m.ano,
        COUNT(*)                                       AS matriculados,
        COUNT(a.aluno_id)                              AS aprovados,
        COUNT(*) - COUNT(a.aluno_id)                   AS nao_aprovados,
        ROUND(100.0 * COUNT(a.aluno_id) / COUNT(*), 1) AS taxa_aprovacao
    FROM matriculados m
    LEFT JOIN aprovado_no_ano a
        ON  a.aluno_id       = m.aluno_id
        AND a.ano_vestibular = m.ano
    GROUP BY m.ano
)
SELECT
    ano,
    matriculados,
    aprovados,
    nao_aprovados,
    taxa_aprovacao,
    ROUND(
        taxa_aprovacao - LAG(taxa_aprovacao) OVER (ORDER BY ano),
        1
    ) AS variacao_pp
FROM por_ano
ORDER BY ano;
