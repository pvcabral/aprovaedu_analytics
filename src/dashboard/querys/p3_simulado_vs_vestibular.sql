-- Pergunta 3: nota de simulado contra nota de vestibular, por aluno e ano.
--
-- Serve para avaliar a calibragem do simulado. A nota de vestibular é dividida por 10
-- para ficar na mesma régua de 0 a 100 do simulado, e diferenca positiva significa que
-- o aluno foi melhor no vestibular.
--
-- Só aparece quem foi aprovado, porque nota de vestibular só existe para aprovado.
-- Isso enviesa a comparação para cima e é limitação da fonte, não escolha.
WITH simulado AS (
    SELECT
        r.aluno_id,
        r.ano,
        COUNT(*)         AS simulados_concluidos,
        AVG(r.nota_norm) AS nota_simulado
    FROM resultados_sim r
    WHERE r.status_realizacao = 'finalizado'
      AND r.ano IS NOT NULL
    GROUP BY r.aluno_id, r.ano
),
vestibular AS (
    SELECT
        aluno_id,
        ano_vestibular             AS ano,
        MAX(nota_final_vestibular) AS nota_vestibular
    FROM aprovacoes
    WHERE nota_final_vestibular IS NOT NULL
    GROUP BY aluno_id, ano_vestibular
)
SELECT
    s.aluno_id,
    s.ano,
    s.simulados_concluidos,
    ROUND(s.nota_simulado::numeric, 1)                            AS nota_simulado,
    v.nota_vestibular,
    ROUND((v.nota_vestibular / 10)::numeric, 1)                   AS vestibular_em_100,
    ROUND((v.nota_vestibular / 10 - s.nota_simulado)::numeric, 1) AS diferenca
FROM simulado s
JOIN vestibular v
    ON  v.aluno_id = s.aluno_id
    AND v.ano      = s.ano
ORDER BY diferenca DESC;
