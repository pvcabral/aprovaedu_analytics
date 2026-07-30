-- Pergunta 2: presença por ano, comparando aprovados e não aprovados.
WITH presenca AS (
    SELECT
        p.aluno_id,
        a.ano,
        COUNT(*) AS aulas_registradas,
        SUM(CASE WHEN p.status_presenca IN ('presente', 'atrasado') THEN 1 ELSE 0 END)
            AS comparecimentos
    FROM presencas_aulas p
    JOIN aulas a ON a.aula_id = p.aula_id
    WHERE a.ano IS NOT NULL
    GROUP BY p.aluno_id, a.ano
),
aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
)
SELECT
    p.ano,
    CASE WHEN ap.aluno_id IS NOT NULL THEN 'Aprovado' ELSE 'Não aprovado' END AS situacao,
    COUNT(*)                       AS alunos,
    SUM(p.aulas_registradas)       AS aulas_registradas,
    SUM(p.comparecimentos)         AS comparecimentos,
    ROUND(100.0 * SUM(p.comparecimentos) / SUM(p.aulas_registradas), 1) AS taxa_presenca
FROM presenca p
LEFT JOIN aprovado_no_ano ap
    ON  ap.aluno_id       = p.aluno_id
    AND ap.ano_vestibular = p.ano
GROUP BY p.ano, (ap.aluno_id IS NOT NULL)
ORDER BY p.ano, situacao;
