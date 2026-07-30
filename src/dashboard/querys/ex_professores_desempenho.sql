-- Análise extra: desempenho por professor, dentro da matéria dele.
--
-- Dois indicadores: comparecimento dos alunos nas aulas que ele deu, e nota nos
-- simulados que ele criou. O intervalo de 95% da nota entra porque sem margem a ordem
-- entre professores sugere diferença onde há variação de amostra.
WITH aula AS (
    SELECT
        a.professor_id,
        COUNT(DISTINCT a.aula_id) AS aulas,
        COUNT(pr.presenca_id)     AS registros_presenca,
        100.0 * SUM(CASE WHEN pr.status_presenca IN ('presente', 'atrasado') THEN 1 ELSE 0 END)
              / COUNT(pr.presenca_id) AS presenca
    FROM aulas a
    JOIN presencas_aulas pr ON pr.aula_id = a.aula_id
    GROUP BY a.professor_id
),
simulado AS (
    SELECT
        s.professor_id,
        COUNT(DISTINCT s.simulado_id)                                   AS simulados,
        COUNT(*)                                                        AS resultados,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.nota_norm)         AS nota_mediana,
        AVG(r.nota_norm)                                                AS nota_media,
        STDDEV_SAMP(r.nota_norm)                                        AS nota_desvio
    FROM simulados s
    JOIN resultados_sim r ON r.simulado_id = s.simulado_id
    WHERE r.status_realizacao = 'finalizado'
    GROUP BY s.professor_id
)
SELECT
    p.professor_id,
    p.nome_professor,
    dm.nome_materia                            AS materia,
    a.aulas,
    ROUND(a.presenca, 1)                       AS presenca,
    s.simulados,
    s.resultados,
    ROUND(s.nota_mediana::numeric, 1)          AS nota_mediana,
    ROUND(s.nota_media, 1)                     AS nota_media,
    ROUND(s.nota_desvio, 1)                    AS nota_desvio,
    ROUND((s.nota_media - 1.96 * s.nota_desvio / SQRT(s.resultados))::numeric, 1)
                                               AS limite_inferior,
    ROUND((s.nota_media + 1.96 * s.nota_desvio / SQRT(s.resultados))::numeric, 1)
                                               AS limite_superior
FROM professores p
JOIN dim_materia dm ON dm.materia_id = p.materia_id
LEFT JOIN aula a     ON a.professor_id = p.professor_id
LEFT JOIN simulado s ON s.professor_id = p.professor_id
ORDER BY nota_mediana DESC NULLS LAST;
