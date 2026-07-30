-- Pergunta 3: a diferença entre vestibular e simulado, ano a ano.
--
-- Mediana e desvio da diferença, mais a proporção de alunos que foi melhor no
-- vestibular. As duas notas na régua de 0 a 100, com a de vestibular dividida por 10.
WITH simulado AS (
    SELECT r.aluno_id, r.ano, AVG(r.nota_norm) AS nota_simulado
    FROM resultados_sim r
    WHERE r.status_realizacao = 'finalizado'
      AND r.ano IS NOT NULL
    GROUP BY r.aluno_id, r.ano
),
vestibular AS (
    SELECT aluno_id, ano_vestibular AS ano, MAX(nota_final_vestibular) AS nota_vestibular
    FROM aprovacoes
    WHERE nota_final_vestibular IS NOT NULL
    GROUP BY aluno_id, ano_vestibular
),
comparacao AS (
    SELECT
        s.ano,
        s.nota_simulado,
        v.nota_vestibular / 10                  AS vestibular_em_100,
        v.nota_vestibular / 10 - s.nota_simulado AS diferenca
    FROM simulado s
    JOIN vestibular v ON v.aluno_id = s.aluno_id AND v.ano = s.ano
)
SELECT
    ano,
    COUNT(*)                                                                    AS alunos,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nota_simulado)::numeric, 1)     AS simulado_mediana,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY vestibular_em_100)::numeric, 1) AS vestibular_mediana,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY diferenca)::numeric, 1)         AS diferenca_mediana,
    ROUND(STDDEV_SAMP(diferenca)::numeric, 1)                                   AS diferenca_desvio,
    ROUND(100.0 * SUM(CASE WHEN diferenca > 0 THEN 1 ELSE 0 END) / COUNT(*), 1)  AS pct_melhor_no_vestibular
FROM comparacao
GROUP BY ano
ORDER BY ano;
