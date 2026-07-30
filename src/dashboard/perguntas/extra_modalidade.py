"""Análise extra: frequência e aprovação por modelo de ensino."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, graficos, tema

QUERY_FREQUENCIA = "ex_modalidade_frequencia"
QUERY_APROVACAO = "ex_modalidade_aprovacao"

SO_ONLINE, PRESENCIAL_HIBRIDO = "Só online", "Presencial e híbrido"


def grafico_frequencia_por_modalidade(frequencia: pd.DataFrame) -> go.Figure:
    """Comparecimento por modalidade de aula e ano, na escala fixa de 75 a 95.

    Args:
        frequencia: uma linha por modalidade e ano.

    Returns:
        A figura montada.
    """
    matriz = frequencia.pivot(index="modalidade", columns="ano", values="presenca")
    matriz = matriz.loc[matriz.mean(axis=1).sort_values(ascending=False).index]
    return graficos.mapa_de_calor(
        matriz, rotulo_valor="presença", faixa=(75, 95), altura=300, margem_esquerda=110,
    )


def grafico_aprovacao_por_modelo(aprovacao: pd.DataFrame) -> go.Figure:
    """Taxa de aprovação dos dois modelos de ensino, ano a ano.

    Args:
        aprovacao: uma linha por modelo de ensino e ano.

    Returns:
        A figura montada.
    """
    largo = aprovacao.pivot(index="ano", columns="modelo_de_ensino",
                            values="taxa_aprovacao")
    largo = largo.sort_index(ascending=False)
    for grupo in (SO_ONLINE, PRESENCIAL_HIBRIDO):
        if grupo not in largo.columns:
            largo[grupo] = pd.NA
    return graficos.haltere(
        largo,
        grupos=(SO_ONLINE, PRESENCIAL_HIBRIDO),
        titulo_x="taxa de aprovação",
        faixa_x=(0, 60),
        altura=320,
        margem_esquerda=64,
        sufixo="%",
    )


def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto(frequencia: pd.DataFrame, aprovacao: pd.DataFrame) -> str:
    """Monta o texto da análise.

    Returns:
        O texto em markdown.
    """
    por_modalidade = frequencia.groupby("modalidade").apply(
        lambda g: 100 * g.comparecimentos.sum() / g.registros.sum(), include_groups=False
    )
    faixa_freq = por_modalidade.max() - por_modalidade.min()

    totais = aprovacao.groupby("modelo_de_ensino").agg(
        alunos=("alunos", "sum"), aprovados=("aprovados", "sum")
    )
    totais["taxa"] = 100 * totais.aprovados / totais.alunos
    largo = aprovacao.pivot(index="ano", columns="modelo_de_ensino", values="taxa_aprovacao")
    anos_comparaveis = largo.dropna().shape[0]
    online_maior = int((largo[SO_ONLINE] > largo[PRESENCIAL_HIBRIDO]).sum()) \
        if SO_ONLINE in largo and PRESENCIAL_HIBRIDO in largo else 0

    return f"""
**A frequência não muda com a modalidade da aula.** Somando os cinco anos, o
comparecimento fica entre {_num(por_modalidade.min())}% e {_num(por_modalidade.max())}%
entre as modalidades, {_num(faixa_freq)} ponto percentual de diferença entre a maior e a
menor. Aula online não tem mais falta que aula presencial, e o padrão se repete em todos
os anos. Vale dizer que 'sem registro' é modalidade não informada na origem, e aparece no
gráfico em vez de ser escondida.

**Na aprovação, a base só permite comparar dois grupos, não três.** A modalidade é
atributo da oferta, e olhando as combinações que existem de fato, um aluno ou fez tudo
online, ou fez presencial e híbrido ao mesmo tempo. Nenhum aluno fez só presencial, e
nenhum fez só híbrido. Isso vem da estrutura das unidades: as ofertas online estão todas
na unidade Online, e as unidades físicas oferecem presencial e híbrido lado a lado. Logo,
separar presencial de híbrido por aluno é impossível aqui.

**E entre esses dois grupos, a diferença é pequena.** No período, quem estudou só online
teve {_num(totais.loc[SO_ONLINE, "taxa"])}% de aprovação contra
{_num(totais.loc[PRESENCIAL_HIBRIDO, "taxa"])}% de quem estudou em unidade física, com
{int(totais.loc[SO_ONLINE, "alunos"])} e {int(totais.loc[PRESENCIAL_HIBRIDO, "alunos"])}
alunos respectivamente. Ano a ano os dois grupos trocam de posição: em {online_maior} dos
{anos_comparaveis} anos comparáveis o grupo online ficou à frente. Em 2024 não houve
aluno exclusivamente online, então esse ano não entra na comparação.
"""


def renderizar() -> None:
    """Renderiza a página de modalidade de ensino."""
    st.subheader("Frequência e aprovação por modelo de ensino")
    st.caption(
        "Frequência usa a modalidade de cada aula, onde os grupos não se sobrepõem. "
        "Aprovação usa a modalidade das ofertas do aluno, e aí a base só separa dois "
        "grupos, pelo motivo explicado abaixo do segundo gráfico."
    )

    frequencia = dados.consultar(QUERY_FREQUENCIA)
    aprovacao = dados.consultar(QUERY_APROVACAO)

    por_modalidade = frequencia.groupby("modalidade").apply(
        lambda g: 100 * g.comparecimentos.sum() / g.registros.sum(), include_groups=False
    )
    totais = aprovacao.groupby("modelo_de_ensino").agg(
        alunos=("alunos", "sum"), aprovados=("aprovados", "sum")
    )
    totais["taxa"] = 100 * totais.aprovados / totais.alunos

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Diferença de frequência entre modalidades",
        f"{por_modalidade.max() - por_modalidade.min():.1f} pp".replace(".", ","),
        help="Entre a modalidade de aula com maior e com menor comparecimento, "
             "somando os cinco anos.",
    )
    col2.metric(
        f"Aprovação, {SO_ONLINE.lower()}",
        f"{totais.loc[SO_ONLINE, 'taxa']:.1f}%".replace(".", ","),
        help=f"{int(totais.loc[SO_ONLINE, 'alunos'])} alunos no período, contando cada "
             "aluno uma vez por ano.",
    )
    col3.metric(
        f"Aprovação, {PRESENCIAL_HIBRIDO.lower()}",
        f"{totais.loc[PRESENCIAL_HIBRIDO, 'taxa']:.1f}%".replace(".", ","),
        help=f"{int(totais.loc[PRESENCIAL_HIBRIDO, 'alunos'])} alunos no período, "
             "contando cada aluno uma vez por ano.",
    )

    st.divider()
    st.markdown("**Comparecimento por modalidade da aula**")
    st.caption(
        "cada registro de presença pertence a uma aula com uma única modalidade, "
        "então aqui as três modalidades são comparáveis"
    )
    st.plotly_chart(grafico_frequencia_por_modalidade(frequencia),
                    use_container_width=True, config={"displayModeBar": False})

    st.markdown("**Aprovação por modelo de ensino do aluno**")
    st.caption("a distância entre as duas marcas é a diferença entre os grupos naquele ano")
    st.plotly_chart(grafico_aprovacao_por_modelo(aprovacao),
                    use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver os números em tabela"):
        st.markdown("**Frequência por modalidade e ano**")
        st.dataframe(
            frequencia.rename(columns={
                "modalidade": "Modalidade da aula", "ano": "Ano", "aulas": "Aulas",
                "registros": "Registros", "comparecimentos": "Comparecimentos",
                "presenca": "Presença (%)",
            }),
            hide_index=True, use_container_width=True,
        )
        st.markdown("**Aprovação por modelo de ensino e ano**")
        st.dataframe(
            aprovacao.rename(columns={
                "modelo_de_ensino": "Modelo de ensino", "ano": "Ano",
                "alunos": "Alunos", "aprovados": "Aprovados",
                "taxa_aprovacao": "Taxa de aprovação (%)",
            }),
            hide_index=True, use_container_width=True,
        )

    st.divider()
    st.markdown("#### O que os dados mostram")
    st.markdown(_texto(frequencia, aprovacao))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        for nome in (QUERY_FREQUENCIA, QUERY_APROVACAO):
            st.caption(f"`src/dashboard/querys/{nome}.sql`")
            st.code(dados.ler_sql(nome), language="sql")
