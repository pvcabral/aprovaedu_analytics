-- Análise extra: frequência dos alunos por modalidade de aula, em cada ano.
--
-- A modalidade vem da aula, e não da oferta: cada registro de presença pertence a uma
-- aula com uma única modalidade, então os grupos não se sobrepõem.
--
-- 'sem registro' é modalidade não informada na origem, e fica visível em vez de ser
-- descartada.
SELECT
    a.modalidade_aula                       AS modalidade,
    a.ano,
    COUNT(DISTINCT a.aula_id)               AS aulas,
    COUNT(*)                                AS registros,
    SUM(CASE WHEN p.status_presenca IN ('presente', 'atrasado') THEN 1 ELSE 0 END)
                                            AS comparecimentos,
    ROUND(100.0 * SUM(CASE WHEN p.status_presenca IN ('presente', 'atrasado') THEN 1 ELSE 0 END)
          / COUNT(*), 1)                    AS presenca
FROM presencas_aulas p
JOIN aulas a ON a.aula_id = p.aula_id
WHERE a.ano IS NOT NULL
GROUP BY a.modalidade_aula, a.ano
ORDER BY a.modalidade_aula, a.ano;
