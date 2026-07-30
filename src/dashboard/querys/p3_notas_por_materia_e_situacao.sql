-- Pergunta 3: nota por matéria e ano, separando quem passou de quem não passou.
--
-- Se alguma matéria discrimina o resultado no vestibular, a mediana dos aprovados nela
-- ficaria acima da dos não aprovados, ano após ano.
--
-- O grão é (aluno, ano, matéria), então um aluno que fez muitos simulados não pesa mais
-- que os outros na mediana do grupo.
WITH nota_por_aluno AS (
    SELECT
        r.aluno_id,
        r.ano,
        dm.nome_materia,
        AVG(r.nota_norm) AS nota
    FROM resultados_sim r
    JOIN simulados s    ON s.simulado_id = r.simulado_id
    JOIN dim_materia dm ON dm.materia_id = s.materia_id
    WHERE r.status_realizacao = 'finalizado'
      AND r.ano IS NOT NULL
    GROUP BY r.aluno_id, r.ano, dm.nome_materia
),
aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
)
SELECT
    n.nome_materia,
    n.ano,
    CASE WHEN a.aluno_id IS NOT NULL THEN 'Aprovado' ELSE 'Não aprovado' END AS situacao,
    COUNT(*)                                                            AS alunos,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY n.nota)::numeric, 1) AS mediana,
    ROUND(STDDEV_SAMP(n.nota)::numeric, 1)                              AS desvio
FROM nota_por_aluno n
LEFT JOIN aprovado_no_ano a
    ON  a.aluno_id       = n.aluno_id
    AND a.ano_vestibular = n.ano
GROUP BY n.nome_materia, n.ano, 3
ORDER BY n.nome_materia, n.ano, situacao;
