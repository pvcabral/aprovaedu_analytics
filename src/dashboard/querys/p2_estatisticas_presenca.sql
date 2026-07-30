-- Pergunta 2: média, desvio e correlação da presença, por situação no vestibular.
--
-- correlacao é a correlação de Pearson entre a presença do aluno (contínua) e a
-- aprovação (1 se passou, 0 se não), calculada pela função CORR. Vai de -1 a +1, e
-- perto de zero significa que a presença não diz nada sobre a chance de passar.
-- O valor se repete nas linhas porque é calculado sobre a base inteira: separar por
-- situação zeraria a variação da aprovação dentro de cada grupo.
WITH presenca AS (
    SELECT
        p.aluno_id,
        a.ano,
        100.0 * SUM(CASE WHEN p.status_presenca IN ('presente', 'atrasado') THEN 1 ELSE 0 END)
              / COUNT(*) AS taxa_presenca
    FROM presencas_aulas p
    JOIN aulas a ON a.aula_id = p.aula_id
    WHERE a.ano IS NOT NULL
    GROUP BY p.aluno_id, a.ano
),
aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
),
base AS (
    SELECT
        p.taxa_presenca,
        CASE WHEN ap.aluno_id IS NOT NULL THEN 1 ELSE 0 END AS aprovado
    FROM presenca p
    LEFT JOIN aprovado_no_ano ap
        ON  ap.aluno_id       = p.aluno_id
        AND ap.ano_vestibular = p.ano
),
por_situacao AS (
    SELECT
        CASE WHEN aprovado = 1 THEN 'Aprovado' ELSE 'Não aprovado' END AS situacao,
        COUNT(*)                                  AS alunos,
        ROUND(AVG(taxa_presenca), 2)              AS presenca_media,
        ROUND(STDDEV_SAMP(taxa_presenca), 2)      AS desvio_padrao
    FROM base
    GROUP BY aprovado
),
correlacao AS (
    SELECT ROUND(CORR(aprovado, taxa_presenca)::numeric, 4) AS correlacao
    FROM base
)
SELECT
    s.situacao,
    s.alunos,
    s.presenca_media,
    s.desvio_padrao,
    c.correlacao
FROM por_situacao s
CROSS JOIN correlacao c
ORDER BY s.situacao;
