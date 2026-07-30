-- Pergunta 3: nota de vestibular dos aprovados em cada ano, todos os cursos juntos.
--
-- Junta os cursos porque só assim há volume por ano para mediana e desvio significarem
-- algo.
SELECT
    ano_vestibular                                                    AS ano,
    COUNT(*)                                                          AS aprovados,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nota_final_vestibular)::numeric, 1)
                                                                      AS mediana,
    ROUND(AVG(nota_final_vestibular), 1)                              AS media,
    ROUND(STDDEV_SAMP(nota_final_vestibular), 1)                      AS desvio,
    ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY nota_final_vestibular)::numeric, 1)
                                                                      AS percentil_10,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY nota_final_vestibular)::numeric, 1)
                                                                      AS percentil_90
FROM aprovacoes
WHERE nota_final_vestibular IS NOT NULL
GROUP BY ano_vestibular
ORDER BY ano;
