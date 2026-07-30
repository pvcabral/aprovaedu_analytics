-- Pergunta 3: aprovações por curso em cada ano.
--
-- Contagem de aprovados, o indicador de curso que não depende de estimativa. A mediana
-- e o desvio saem na consulta para conferência, mas com poucas unidades por curso e ano
-- não descrevem nada: para nota por curso use p3_notas_vestibular_por_curso.sql.
SELECT
    curso_aprovado,
    ano_vestibular                                                    AS ano,
    COUNT(*)                                                          AS aprovados,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nota_final_vestibular)::numeric, 1)
                                                                      AS mediana,
    ROUND(STDDEV_SAMP(nota_final_vestibular), 1)                      AS desvio
FROM aprovacoes
GROUP BY curso_aprovado, ano_vestibular
ORDER BY curso_aprovado, ano;
