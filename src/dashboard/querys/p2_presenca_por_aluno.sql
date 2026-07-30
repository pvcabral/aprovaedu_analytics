-- Pergunta 2: presença de cada aluno em cada ano, com a situação no vestibular.
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
    p.aluno_id,
    p.ano,
    CASE WHEN ap.aluno_id IS NOT NULL THEN 'Aprovado' ELSE 'Não aprovado' END AS situacao,
    p.aulas_registradas,
    p.comparecimentos,
    ROUND(100.0 * p.comparecimentos / p.aulas_registradas, 1) AS taxa_presenca
FROM presenca p
LEFT JOIN aprovado_no_ano ap
    ON  ap.aluno_id       = p.aluno_id
    AND ap.ano_vestibular = p.ano
ORDER BY p.ano, taxa_presenca DESC;
