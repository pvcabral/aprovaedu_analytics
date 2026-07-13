"""Funções de carga de dados do banco para o dashboard Streamlit.

Cada função conecta no banco, roda as consultas necessárias e desconecta
em seguida, o resultado fica em cache (`st.cache_data`) para não reabrir
conexão a cada interação do usuário no Streamlit.
"""

import pandas as pd
import streamlit as st

from src.banco import BancoDados


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_desempenho_por_modalidade() -> pd.DataFrame:
    """Calcula a taxa de aprovação por modalidade de ensino da turma.

    A modalidade (`Presencial` / `Online` / `Híbrido`) vem de
    `ofertas_curso`. Cada matrícula é ligada à sua oferta para pegar a
    modalidade, e a coorte tem grão `(aluno, ano, modalidade)`: o aluno é
    aprovado naquela modalidade/ano se tem aprovação no vestibular do mesmo
    ano (regra `gap = 0`, igual à taxa de aprovação geral). Um aluno
    matriculado em mais de uma modalidade no ano conta em cada uma delas.

    O denominador vem de `matriculas` (amostra curta, poucos alunos) e o
    numerador é conferido contra `aprovacoes` (base completa), então a
    não-aprovação é real. Ainda assim, a base é pequena, leia como
    indício, não número fechado.

    Returns:
        DataFrame com `modalidade`, `matriculas_ano`, `aprovados` e
        `taxa_aprovacao` (percentual, uma casa), uma linha por modalidade.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            WITH coorte AS (
                SELECT DISTINCT m.aluno_id, m.ano, o.modalidade
                FROM matriculas m
                JOIN ofertas_curso o ON o.oferta_id = m.oferta_id
                WHERE m.ano IS NOT NULL AND o.modalidade IS NOT NULL
            ),
            aprovado_no_ano AS (
                SELECT DISTINCT aluno_id, ano_vestibular FROM aprovacoes
            )
            SELECT
                c.modalidade,
                COUNT(*) AS matriculas_ano,
                COUNT(a.aluno_id) AS aprovados,
                ROUND(100.0 * COUNT(a.aluno_id) / COUNT(*), 1) AS taxa_aprovacao
            FROM coorte c
            LEFT JOIN aprovado_no_ano a
                ON a.aluno_id = c.aluno_id
               AND a.ano_vestibular = c.ano
            GROUP BY c.modalidade
            ORDER BY taxa_aprovacao DESC
        """)
    finally:
        banco.desconectar()

    return base.reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_taxa_aprovacao_por_ano() -> pd.DataFrame:
    """Calcula a taxa de aprovação dos alunos matriculados, por ano.

    A coorte tem grão `(aluno_id, ano)`: cada aluno conta uma vez em cada
    ano em que teve matrícula. Um aluno matriculado no ano X é considerado
    aprovado naquele ano se, e somente se, existe uma linha em
    `aprovacoes` com `ano_vestibular = X` para ele (regra de janela
    `gap = 0`: matrícula e aprovação no mesmo ano).

    A regra é intencionalmente conservadora: aprovações em anos diferentes
    do ano da matrícula (`gap != 0`) não são atribuídas, porque a amostra
    não permite validar com segurança a qual matrícula elas correspondem
    (um mesmo aluno tem várias matrículas em anos distintos). Matriculado
    sem aprovação no mesmo ano entra na coorte como não-aprovado.

    O denominador é `matriculas` (tabela amostrada); o numerador consulta
    `aprovacoes` (tabela completa da base), então a não-aprovação é real,
    não um efeito de dados faltando. Ainda assim, a amostra de matrículas
    cobre poucos alunos, a taxa é uma estimativa, não o número fechado do
    curso (ver o N de cada ano).

    Returns:
        DataFrame com `ano`, `matriculados`, `aprovados` e `taxa_aprovacao`
        (percentual, uma casa decimal), uma linha por ano.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            WITH coorte AS (
                SELECT DISTINCT aluno_id, ano
                FROM matriculas
                WHERE ano IS NOT NULL AND aluno_id IS NOT NULL
            ),
            aprovado_no_ano AS (
                SELECT DISTINCT aluno_id, ano_vestibular
                FROM aprovacoes
            )
            SELECT
                c.ano,
                COUNT(*) AS matriculados,
                COUNT(a.aluno_id) AS aprovados
            FROM coorte c
            LEFT JOIN aprovado_no_ano a
                ON a.aluno_id = c.aluno_id
               AND a.ano_vestibular = c.ano
            GROUP BY c.ano
            ORDER BY c.ano
        """)
    finally:
        banco.desconectar()

    base["taxa_aprovacao"] = (base["aprovados"] / base["matriculados"] * 100).round(1)
    return base.sort_values("ano").reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_desempenho_por_materia() -> pd.DataFrame:
    """Calcula nota média e mediana de simulado por matéria.

    O desempenho vem dos resultados de simulado (`resultados_sim.nota`),
    ligados à matéria via `simulados.materia_id`. Considera só os simulados
    de fato **finalizados** (`status_realizacao = 'finalizado'`).

    As notas acima do limite da escala (100) não são descartadas: são
    **capadas no próprio limite** (`LEAST(nota, 100)`), para não perder o
    registro do aluno nem deixar um outlier inflar a média. A mediana entra
    como estatística complementar à média, mais robusta a valores extremos.

    Atenção: a amostra de `resultados_sim` (500 de 21510) cobre resultados
    de poucas matérias, na amostra atual, só matemática e física têm
    resultado registrado. As demais não aparecem, então a leitura é
    parcial, não o retrato de todas as disciplinas.

    Returns:
        DataFrame com `nome_materia`, `n_resultados`, `nota_media`,
        `nota_mediana` e `acertos_medio`, uma linha por matéria.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            SELECT
                dm.nome_materia,
                COUNT(*) AS n_resultados,
                ROUND(AVG(LEAST(r.nota, 100)), 1) AS nota_media,
                ROUND(
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LEAST(r.nota, 100))::numeric,
                    1
                ) AS nota_mediana,
                ROUND(AVG(r.acertos), 1) AS acertos_medio
            FROM resultados_sim r
            JOIN simulados s ON s.simulado_id = r.simulado_id
            JOIN dim_materia dm ON dm.materia_id = s.materia_id
            WHERE r.status_realizacao = 'finalizado'
            GROUP BY dm.nome_materia
            ORDER BY nota_media DESC
        """)
    finally:
        banco.desconectar()

    return base.reset_index(drop=True)


ORDEM_FAIXA_SIMULADO = ["Abaixo de 50", "50 a 60", "60 a 70", "70 ou mais"]


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_aprovacao_por_faixa_simulado() -> pd.DataFrame:
    """Calcula a taxa de aprovação por faixa de nota de simulado do aluno.

    A coorte tem grão `(aluno, ano)`: para cada aluno/ano com simulado
    finalizado, calcula a nota média (capada em 100), classifica em faixas
    e mede a taxa de aprovação, respondendo se ir melhor nos simulados
    está associado a passar no vestibular. "Aprovado" é conferido no
    **mesmo ano** do simulado (`resultados_sim.ano = aprovacoes.ano_vestibular`),
    para não comparar um simulado de um ano com uma aprovação de outro.
    A aprovação vem de `aprovacoes` (base completa), então a não-aprovação
    é real.

    A amostra de simulado só cobre matemática/física e poucas dezenas de
    alunos (na amostra atual, só 2021), então o resultado é indício, não
    prova.

    Returns:
        DataFrame com `faixa_nota`, `n_alunos`, `aprovados` e
        `taxa_aprovacao` (percentual), uma linha por faixa.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            WITH nota_aluno_ano AS (
                SELECT r.aluno_id, r.ano, AVG(LEAST(r.nota, 100)) AS nota_media
                FROM resultados_sim r
                JOIN simulados s ON s.simulado_id = r.simulado_id
                WHERE r.status_realizacao = 'finalizado' AND r.ano IS NOT NULL
                GROUP BY r.aluno_id, r.ano
            ),
            aprovado_no_ano AS (
                SELECT DISTINCT aluno_id, ano_vestibular FROM aprovacoes
            ),
            classificado AS (
                SELECT
                    CASE
                        WHEN na.nota_media < 50 THEN 'Abaixo de 50'
                        WHEN na.nota_media < 60 THEN '50 a 60'
                        WHEN na.nota_media < 70 THEN '60 a 70'
                        ELSE '70 ou mais'
                    END AS faixa_nota,
                    CASE WHEN a.aluno_id IS NOT NULL THEN 1 ELSE 0 END AS aprovado
                FROM nota_aluno_ano na
                LEFT JOIN aprovado_no_ano a
                    ON a.aluno_id = na.aluno_id
                   AND a.ano_vestibular = na.ano
            )
            SELECT
                faixa_nota,
                COUNT(*) AS n_alunos,
                SUM(aprovado) AS aprovados,
                ROUND(100.0 * SUM(aprovado) / COUNT(*), 1) AS taxa_aprovacao
            FROM classificado
            GROUP BY faixa_nota
        """)
    finally:
        banco.desconectar()

    base["faixa_nota"] = pd.Categorical(
        base["faixa_nota"], categories=ORDEM_FAIXA_SIMULADO, ordered=True
    )
    return base.sort_values("faixa_nota").reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_simulado_vs_vestibular() -> pd.DataFrame:
    """Compara a nota de simulado com a nota do vestibular dos aprovados.

    Para cada aluno aprovado que também tem simulado no mesmo ano, traz a
    nota média de simulado (0-100, capada) e a nota final de vestibular
    daquele ano. O casamento é por `(aluno, ano)`, então o simulado do ano X
    só é comparado com a aprovação do vestibular do ano X.

    Como o vestibular está numa escala ~0-1000 e o simulado em 0-100, a nota
    de vestibular é normalizada para 0-100 (÷10). A `diferenca` é
    `vestibular_norm - simulado` (positiva quando o aluno foi melhor no
    vestibular do que nos simulados).

    Returns:
        DataFrame com `aluno_id`, `ano`, `nota_simulado`, `nota_vestibular`
        (escala original), `nota_vestibular_norm` (0-100) e `diferenca`.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            WITH nota_sim AS (
                SELECT r.aluno_id, r.ano, ROUND(AVG(LEAST(r.nota, 100)), 1) AS nota_simulado
                FROM resultados_sim r
                JOIN simulados s ON s.simulado_id = r.simulado_id
                WHERE r.status_realizacao = 'finalizado' AND r.ano IS NOT NULL
                GROUP BY r.aluno_id, r.ano
            ),
            vest AS (
                SELECT aluno_id, ano_vestibular AS ano, MAX(nota_final_vestibular) AS nota_vestibular
                FROM aprovacoes
                WHERE nota_final_vestibular IS NOT NULL
                GROUP BY aluno_id, ano_vestibular
            )
            SELECT ns.aluno_id, ns.ano, ns.nota_simulado, v.nota_vestibular
            FROM nota_sim ns
            JOIN vest v ON v.aluno_id = ns.aluno_id AND v.ano = ns.ano
        """)
    finally:
        banco.desconectar()

    base["nota_vestibular_norm"] = (base["nota_vestibular"] / 10).round(1)
    base["diferenca"] = (base["nota_vestibular_norm"] - base["nota_simulado"]).round(1)
    return base.reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_desempenho_por_curso_aprovado() -> pd.DataFrame:
    """Calcula a nota final média de vestibular por curso da universidade.

    Usa `aprovacoes.nota_final_vestibular` agrupada por `curso_aprovado` (o
    curso da faculdade em que o aluno passou: medicina, direito, etc.).
    Diferente do desempenho por matéria, isto mede o **resultado no
    vestibular** por curso pretendido, não o domínio de disciplina no
    cursinho. Vem de `aprovacoes`, base completa do desafio, então é
    sólido, sem ruído de amostragem.

    Returns:
        DataFrame com `curso_aprovado`, `n_aprovados` e `nota_media`,
        uma linha por curso, ordenado por nota.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            SELECT
                curso_aprovado,
                COUNT(*) AS n_aprovados,
                ROUND(AVG(nota_final_vestibular), 1) AS nota_media
            FROM aprovacoes
            WHERE nota_final_vestibular IS NOT NULL
            GROUP BY curso_aprovado
            ORDER BY nota_media DESC
        """)
    finally:
        banco.desconectar()

    return base.reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_aprovados_por_bolsa() -> pd.DataFrame:
    """Conta os aprovados por ano, agrupados em com bolsa / sem bolsa.

    `bolsa_aprovacao` traz a situação de bolsa de cada aprovação (não se o
    aluno passou, toda linha de `aprovacoes` já é um aprovado). Os valores
    são consolidados em três categorias para responder "o aprovado passou
    com bolsa ou não":

    - "Com bolsa": bolsa integral (`sim`) ou parcial (`parcial`).
    - "Sem bolsa": aprovado sem bolsa (`nao`).
    - "Não informado": aprovação sem essa informação registrada.

    Usa só `aprovacoes`, que é a base completa do desafio, sem ruído de
    amostragem entre tabelas.

    Returns:
        DataFrame com `ano`, `categoria_bolsa` e `n_aprovados`, uma linha
        por combinação ano/categoria.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            SELECT
                ano_vestibular AS ano,
                CASE
                    WHEN bolsa_aprovacao IN ('sim', 'parcial') THEN 'Com bolsa'
                    WHEN bolsa_aprovacao = 'nao' THEN 'Sem bolsa'
                    ELSE 'Não informado'
                END AS categoria_bolsa,
                COUNT(*) AS n_aprovados
            FROM aprovacoes
            GROUP BY ano_vestibular, categoria_bolsa
            ORDER BY ano_vestibular, categoria_bolsa
        """)
    finally:
        banco.desconectar()

    return base.sort_values(["categoria_bolsa", "ano"]).reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Carregando dados do banco...")
def carregar_presenca_aprovacao() -> pd.DataFrame:
    """Compara, por ano, a taxa de presença de aprovados e não aprovados.

    A presença é amarrada ao ano em que a aula foi ofertada: cada registro
    de `presencas_aulas` é ligado à sua aula (`aula_id`) para pegar o
    `aulas.ano`. Assim a presença do aluno em um ano só é comparada com a
    aprovação no vestibular **daquele mesmo ano** (regra de janela
    `gap = 0`), evitando o descasamento de comparar presença de um ano com
    uma aprovação de outro. Cada `presenca_id` é único, então não há
    contagem repetida de aula.

    A métrica é **comparecimento**: contam como frequência tanto `presente`
    quanto `atrasado`, já que o aluno atrasado esteve na aula. Os demais
    status ficam de fora do numerador — falta justificada continua sendo
    não-comparecimento, só com explicação por trás.

    Considera **apenas os alunos que de fato têm presença registrada**.
    Essa amostra é curta: a tabela de presenças vem amostrada e ainda perde,
    na carga, os alunos cujo `aluno_id` não existe no cadastro de
    `estudantes`. Além disso, as aulas amostradas cobrem poucos anos (na
    amostra atual, só 2021), então o resultado é um indício, não um número
    fechado.

    A situação de aprovação é binária (`Aprovado` / `Não aprovado`) e é
    conferida contra `aprovacoes`, base completa do desafio, logo "não
    aprovado" é real, não dado faltando por amostragem. A taxa de presença
    é agregada: soma das aulas frequentadas dividida pela soma das
    aulas registradas do grupo, para um aluno com poucos registros não
    dominar a média.

    Returns:
        DataFrame com `ano`, `situacao`, `n_alunos`, `total_aulas`,
        `aulas_presentes` e `taxa_presenca` (percentual, uma casa),
        uma linha por combinação ano/situação.
    """
    banco = BancoDados()
    try:
        banco.conectar()
        base = banco.consultar("""
            WITH presenca_por_aluno_ano AS (
                SELECT
                    p.aluno_id,
                    a.ano AS ano,
                    COUNT(*) AS total_aulas,
                    SUM(CASE WHEN LOWER(TRIM(p.status_presenca))
                                  IN ('presente', 'atrasado')
                             THEN 1 ELSE 0 END) AS aulas_presentes
                FROM presencas_aulas p
                JOIN aulas a ON a.aula_id = p.aula_id
                WHERE a.ano IS NOT NULL
                GROUP BY p.aluno_id, a.ano
            ),
            aprovado_no_ano AS (
                SELECT DISTINCT aluno_id, ano_vestibular FROM aprovacoes
            )
            SELECT
                pa.ano,
                CASE WHEN ap.aluno_id IS NOT NULL THEN 'Aprovado' ELSE 'Não aprovado' END
                    AS situacao,
                COUNT(*) AS n_alunos,
                SUM(pa.total_aulas) AS total_aulas,
                SUM(pa.aulas_presentes) AS aulas_presentes
            FROM presenca_por_aluno_ano pa
            LEFT JOIN aprovado_no_ano ap
                ON ap.aluno_id = pa.aluno_id
               AND ap.ano_vestibular = pa.ano
            GROUP BY pa.ano, (ap.aluno_id IS NOT NULL)
            ORDER BY pa.ano
        """)
    finally:
        banco.desconectar()

    base["taxa_presenca"] = (base["aulas_presentes"] / base["total_aulas"] * 100).round(1)
    ordem = ["Aprovado", "Não aprovado"]
    base["situacao"] = pd.Categorical(base["situacao"], categories=ordem, ordered=True)
    return base.sort_values(["ano", "situacao"]).reset_index(drop=True)