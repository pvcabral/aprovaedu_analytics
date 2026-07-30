-- Pergunta 3: nota de simulado por matéria em cada ano.
--
-- Usa nota_norm, e não nota: redação é corrigida de 0 a 1000 e as demais de 0 a 100,
-- então a nota crua não é comparável entre matérias.
SELECT
    dm.nome_materia,
    r.ano,
    COUNT(*)                                                                  AS resultados,
    COUNT(DISTINCT r.aluno_id)                                                AS alunos,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.nota_norm)::numeric, 1) AS mediana,
    ROUND(AVG(r.nota_norm), 1)                                                AS media,
    ROUND(STDDEV_SAMP(r.nota_norm), 1)                                        AS desvio,
    ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY r.nota_norm)::numeric, 1) AS percentil_10,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY r.nota_norm)::numeric, 1) AS percentil_90
FROM resultados_sim r
JOIN simulados s    ON s.simulado_id = r.simulado_id
JOIN dim_materia dm ON dm.materia_id = s.materia_id
WHERE r.status_realizacao = 'finalizado'
  AND r.ano IS NOT NULL
GROUP BY dm.nome_materia, r.ano
ORDER BY dm.nome_materia, r.ano;
