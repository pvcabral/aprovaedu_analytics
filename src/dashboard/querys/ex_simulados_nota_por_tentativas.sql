-- Análise extra: a nota melhora com o número de tentativas?
--
-- Serve para saber se tentativa pode ser lida como esforço que rende ou apenas como
-- atrito. O NULLIF existe porque na origem a coluna só tem 1, 2 e 3, e o tratamento
-- preencheu os nulos com 0.
SELECT
    NULLIF(tentativas, 0)                                                      AS tentativas,
    COUNT(*)                                                                   AS resultados,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nota_norm)::numeric, 1)   AS nota_mediana,
    ROUND(STDDEV_SAMP(nota_norm), 1)                                           AS nota_desvio,
    ROUND(AVG(tempo_finalizacao_min), 0)                                       AS tempo_medio_min
FROM resultados_sim
WHERE status_realizacao = 'finalizado'
  AND NULLIF(tentativas, 0) IS NOT NULL
GROUP BY 1
ORDER BY 1;
