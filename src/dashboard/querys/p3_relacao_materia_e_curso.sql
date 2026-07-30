-- Pergunta 3: os aprovados de cada curso vinham fortes em alguma área?
--
-- As áreas seguem a divisão do ENEM. A classificação é feita aqui, e não numa coluna
-- do banco, porque é agrupamento de análise. Agrupar é necessário por amostra: 11
-- matérias por 14 cursos daria células de 2 alunos.
--
-- A nota é padronizada em escore z dentro de cada área e ano, senão o aluno pareceria
-- mais forte na área que dá nota alta para todos. z_medio positivo significa acima da
-- média da área. Valores dentro de dois erros padrão são o que o acaso produz.
WITH nota_por_area AS (
    SELECT
        r.aluno_id,
        r.ano,
        CASE dm.nome_materia
            WHEN 'matematica' THEN 'Exatas'
            WHEN 'quimica'    THEN 'Natureza'
            WHEN 'fisica'     THEN 'Natureza'
            WHEN 'biologia'   THEN 'Natureza'
            WHEN 'historia'   THEN 'Humanas'
            WHEN 'geografia'  THEN 'Humanas'
            WHEN 'filosofia'  THEN 'Humanas'
            WHEN 'sociologia' THEN 'Humanas'
            WHEN 'portugues'  THEN 'Linguagens'
            WHEN 'ingles'     THEN 'Linguagens'
            WHEN 'redacao'    THEN 'Redação'
        END              AS area,
        AVG(r.nota_norm) AS nota
    FROM resultados_sim r
    JOIN simulados s    ON s.simulado_id = r.simulado_id
    JOIN dim_materia dm ON dm.materia_id = s.materia_id
    WHERE r.status_realizacao = 'finalizado'
      AND r.ano IS NOT NULL
    GROUP BY r.aluno_id, r.ano, 3
),
padronizado AS (
    SELECT
        aluno_id,
        ano,
        area,
        (nota - AVG(nota) OVER (PARTITION BY area, ano))
            / STDDEV_SAMP(nota) OVER (PARTITION BY area, ano) AS z
    FROM nota_por_area
),
aprovado AS (
    SELECT DISTINCT aluno_id, ano_vestibular AS ano, curso_aprovado
    FROM aprovacoes
)
SELECT
    a.curso_aprovado,
    p.area,
    COUNT(*)                                AS aprovados,
    ROUND(AVG(p.z)::numeric, 2)             AS z_medio,
    ROUND((1 / SQRT(COUNT(*)))::numeric, 2) AS erro_padrao
FROM padronizado p
JOIN aprovado a
    ON  a.aluno_id = p.aluno_id
    AND a.ano      = p.ano
GROUP BY a.curso_aprovado, p.area
ORDER BY a.curso_aprovado, p.area;
