-- Pergunta 4: todos os fatores testados, na mesma unidade de medida.
--
-- Cada linha compara o grupo alto com o grupo baixo de um fator, em pontos percentuais
-- de taxa de aprovação. Intervalo que contém zero significa fator que não distingue
-- aprovado de não aprovado.
--
-- O erro padrão é o da diferença entre duas proporções:
--     erro = raiz( p1*(1-p1)/n1 + p2*(1-p2)/n2 )
WITH aprovado_no_ano AS (
    SELECT DISTINCT aluno_id, ano_vestibular
    FROM aprovacoes
),
matriculado AS (
    SELECT DISTINCT aluno_id, ano
    FROM matriculas
    WHERE ano IS NOT NULL AND aluno_id IS NOT NULL
),
presenca AS (
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
simulado AS (
    SELECT aluno_id, ano, AVG(nota_norm) AS nota_simulado
    FROM resultados_sim
    WHERE status_realizacao = 'finalizado' AND ano IS NOT NULL
    GROUP BY aluno_id, ano
),
diagnostico AS (
    SELECT aluno_id, ano, AVG(nota_diagnostico) AS nota_diagnostico
    FROM matriculas
    WHERE ano IS NOT NULL AND nota_diagnostico > 0
    GROUP BY aluno_id, ano
),
modelo AS (
    SELECT
        m.aluno_id,
        m.ano,
        CASE WHEN COUNT(DISTINCT o.modalidade) = 1 AND MIN(o.modalidade) = 'Online'
             THEN 'online' ELSE 'fisica' END AS modelo_de_ensino
    FROM matriculas m
    JOIN ofertas_curso o ON o.oferta_id = m.oferta_id
    WHERE m.ano IS NOT NULL AND o.modalidade IS NOT NULL
    GROUP BY m.aluno_id, m.ano
),
base AS (
    SELECT
        t.aluno_id,
        t.ano,
        CASE WHEN ap.aluno_id IS NOT NULL THEN 1 ELSE 0 END AS aprovado,
        pr.taxa_presenca,
        NTILE(4) OVER (ORDER BY si.nota_simulado)    AS quartil_simulado,
        NTILE(4) OVER (ORDER BY di.nota_diagnostico) AS quartil_diagnostico,
        mo.modelo_de_ensino
    FROM matriculado t
    LEFT JOIN aprovado_no_ano ap ON ap.aluno_id = t.aluno_id AND ap.ano_vestibular = t.ano
    LEFT JOIN presenca pr        ON pr.aluno_id = t.aluno_id AND pr.ano = t.ano
    LEFT JOIN simulado si        ON si.aluno_id = t.aluno_id AND si.ano = t.ano
    LEFT JOIN diagnostico di     ON di.aluno_id = t.aluno_id AND di.ano = t.ano
    LEFT JOIN modelo mo          ON mo.aluno_id = t.aluno_id AND mo.ano = t.ano
),
classificado AS (
    SELECT 1 AS ordem, 'Presença nas aulas' AS fator,
           'presença de 90% ou mais' AS rotulo_alto, 'presença abaixo de 78%' AS rotulo_baixo,
           CASE WHEN taxa_presenca >= 90 THEN 'alto'
                WHEN taxa_presenca <  78 THEN 'baixo' END AS grupo,
           aprovado
    FROM base WHERE taxa_presenca IS NOT NULL
    UNION ALL
    SELECT 2, 'Nota de simulado',
           'quarto superior da nota', 'quarto inferior da nota',
           CASE WHEN quartil_simulado = 4 THEN 'alto'
                WHEN quartil_simulado = 1 THEN 'baixo' END,
           aprovado
    FROM base WHERE quartil_simulado IS NOT NULL
    UNION ALL
    SELECT 3, 'Nota diagnóstica na matrícula',
           'quarto superior da nota', 'quarto inferior da nota',
           CASE WHEN quartil_diagnostico = 4 THEN 'alto'
                WHEN quartil_diagnostico = 1 THEN 'baixo' END,
           aprovado
    FROM base WHERE quartil_diagnostico IS NOT NULL
    UNION ALL
    SELECT 4, 'Modelo de ensino',
           'só online', 'presencial e híbrido',
           CASE WHEN modelo_de_ensino = 'online' THEN 'alto' ELSE 'baixo' END,
           aprovado
    FROM base WHERE modelo_de_ensino IS NOT NULL
    UNION ALL
    SELECT 5, 'Ano de matrícula',
           'melhor ano (2021)', 'pior ano (2024)',
           CASE WHEN ano = 2021 THEN 'alto' WHEN ano = 2024 THEN 'baixo' END,
           aprovado
    FROM base
),
agregado AS (
    SELECT
        ordem, fator, rotulo_alto, rotulo_baixo,
        COUNT(*) FILTER (WHERE grupo = 'alto')                          AS n_alto,
        COUNT(*) FILTER (WHERE grupo = 'baixo')                         AS n_baixo,
        AVG(CASE WHEN grupo = 'alto'  THEN aprovado::numeric END)       AS p_alto,
        AVG(CASE WHEN grupo = 'baixo' THEN aprovado::numeric END)       AS p_baixo
    FROM classificado
    WHERE grupo IS NOT NULL
    GROUP BY ordem, fator, rotulo_alto, rotulo_baixo
)
SELECT
    fator,
    rotulo_alto,
    rotulo_baixo,
    n_alto,
    n_baixo,
    ROUND(100 * p_alto, 1)                   AS taxa_alto,
    ROUND(100 * p_baixo, 1)                  AS taxa_baixo,
    ROUND(100 * (p_alto - p_baixo), 1)       AS diferenca_pp,
    ROUND(100 * SQRT(p_alto * (1 - p_alto) / n_alto
                   + p_baixo * (1 - p_baixo) / n_baixo), 1) AS erro_padrao,
    ROUND(100 * ((p_alto - p_baixo)
        - 1.96 * SQRT(p_alto * (1 - p_alto) / n_alto
                    + p_baixo * (1 - p_baixo) / n_baixo)), 1) AS limite_inferior,
    ROUND(100 * ((p_alto - p_baixo)
        + 1.96 * SQRT(p_alto * (1 - p_alto) / n_alto
                    + p_baixo * (1 - p_baixo) / n_baixo)), 1) AS limite_superior
FROM agregado
ORDER BY ordem;
