-- Análise extra: quantas matérias cada professor declara ensinar e em quantas dá aula.
--
-- professores.materia_id é a matéria principal e professor_materia vem de
-- materias_ensina. Comparar as duas com a matéria das aulas responde se alguém leciona
-- fora da própria matéria.
SELECT
    p.professor_id,
    p.nome_professor,
    dm.nome_materia                                   AS materia_principal,
    COUNT(DISTINCT pm.materia_id)                     AS materias_declaradas,
    COUNT(DISTINCT a.materia_id)                      AS materias_com_aula,
    COUNT(DISTINCT a.aula_id)                         AS aulas,
    COUNT(DISTINCT a.aula_id) FILTER (WHERE a.materia_id <> p.materia_id)
                                                      AS aulas_fora_da_principal
FROM professores p
JOIN dim_materia dm       ON dm.materia_id = p.materia_id
LEFT JOIN professor_materia pm ON pm.professor_id = p.professor_id
LEFT JOIN aulas a         ON a.professor_id = p.professor_id
GROUP BY p.professor_id, p.nome_professor, dm.nome_materia
ORDER BY materias_declaradas DESC, p.nome_professor;
