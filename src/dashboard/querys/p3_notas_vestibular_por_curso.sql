-- Pergunta 3: nota de vestibular por curso, somando os cinco anos.
--
-- Os anos são somados porque por curso e ano sobram poucas unidades de aprovado, e
-- mediana de meia dúzia de valores não descreve nada. A evolução anual está em
-- p3_notas_vestibular_por_ano.sql.
--
-- A nota por curso reflete a concorrência do curso, não a qualidade do preparo.
SELECT
    curso_aprovado,
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
GROUP BY curso_aprovado
ORDER BY mediana DESC;
