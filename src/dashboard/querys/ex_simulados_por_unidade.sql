-- Análise extra: desempenho nos simulados por unidade de aplicação.
--
-- Mesmos indicadores da consulta por dispositivo. tentativas usa NULLIF porque na
-- origem a coluna só tem 1, 2 e 3, e o tratamento preencheu os nulos com 0.
SELECT
    unidade_aplicacao,
    COUNT(*)                                                                   AS resultados,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nota_norm)::numeric, 1)   AS nota_mediana,
    ROUND(STDDEV_SAMP(nota_norm), 1)                                           AS nota_desvio,
    ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY nota_norm)::numeric, 1)  AS nota_percentil_10,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY nota_norm)::numeric, 1)  AS nota_percentil_90,
    ROUND(AVG(NULLIF(tentativas, 0))::numeric, 2)                              AS tentativas_media,
    COUNT(*) FILTER (WHERE NULLIF(tentativas, 0) IS NULL)                      AS sem_tentativa_registrada,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status_realizacao = 'finalizado') / COUNT(*), 1)
                                                                               AS pct_concluido
FROM resultados_sim
GROUP BY unidade_aplicacao
ORDER BY nota_mediana DESC;
