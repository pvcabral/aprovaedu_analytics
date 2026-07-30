-- Pergunta 2: taxa de aprovação por faixa de presença do aluno.
WITH presenca AS (
    SELECT
        p.aluno_id,
        a.ano,
        COUNT(*) AS aulas_registradas,
        SUM(CASE WHEN p.status_presenca IN ('presente', 'atrasado') THEN 1 ELSE 0 END)
            AS comparecimentos
    FROM presencas_aulas p
    JOIN aulas a ON a.aula_id = p.aula_id
    WHERE a.ano IS NOT NULL
    GROUP BY p.aluno_id, a.ano
),
aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
),
classificado AS (
    SELECT
        WIDTH_BUCKET(100.0 * p.comparecimentos / p.aulas_registradas,
                     ARRAY[78, 82, 86, 90]) AS faixa_ordem,
        CASE WHEN ap.aluno_id IS NOT NULL THEN 1 ELSE 0 END AS aprovado
    FROM presenca p
    LEFT JOIN aprovado_no_ano ap
        ON  ap.aluno_id       = p.aluno_id
        AND ap.ano_vestibular = p.ano
)
SELECT
    faixa_ordem,
    CASE faixa_ordem
        WHEN 0 THEN 'Abaixo de 78%'
        WHEN 1 THEN '78% a 82%'
        WHEN 2 THEN '82% a 86%'
        WHEN 3 THEN '86% a 90%'
        WHEN 4 THEN '90% ou mais'
    END                                        AS faixa_presenca,
    COUNT(*)                                   AS alunos,
    SUM(aprovado)                              AS aprovados,
    ROUND(100.0 * SUM(aprovado) / COUNT(*), 1) AS taxa_aprovacao
FROM classificado
GROUP BY faixa_ordem
ORDER BY faixa_ordem;
