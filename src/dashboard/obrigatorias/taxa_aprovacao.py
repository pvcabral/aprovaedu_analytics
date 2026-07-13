"""Pergunta obrigatória 1: taxa de aprovação dos matriculados e o recorte com/sem bolsa."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.dados import (
    carregar_aprovados_por_bolsa,
    carregar_taxa_aprovacao_por_ano,
)

CORES_BOLSA = {
    "Com bolsa": "#4C78A8",
    "Sem bolsa": "#E45756",
    "Não informado": "#B3B3B3",
}
ORDEM_BOLSA = ["Com bolsa", "Sem bolsa", "Não informado"]


def _grafico_taxa_aprovacao(dados) -> go.Figure:
    """Monta o gráfico de barras da taxa de aprovação dos matriculados por ano."""
    dados = dados.copy()
    dados["ano"] = dados["ano"].astype(str)

    fig = px.bar(
        dados,
        x="ano",
        y="taxa_aprovacao",
        text="taxa_aprovacao",
        labels={"ano": "Ano da matrícula", "taxa_aprovacao": "Taxa de aprovação (%)"},
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        marker_color="#4C78A8",
    )
    fig.update_layout(yaxis_range=[0, 100])
    return fig


def _grafico_aprovados_por_bolsa(dados) -> go.Figure:
    """Monta o gráfico de linhas dos aprovados com/sem bolsa ao longo dos anos.

    Uma linha por categoria (com bolsa, sem bolsa, não informado) deixa
    ver se o número de aprovados subiu ou caiu em cada situação de bolsa
    de um ano para o outro.
    """
    dados = dados.copy()
    dados["ano"] = dados["ano"].astype(str)
    anos = sorted(dados["ano"].unique())

    fig = px.line(
        dados,
        x="ano",
        y="n_aprovados",
        color="categoria_bolsa",
        markers=True,
        color_discrete_map=CORES_BOLSA,
        category_orders={"categoria_bolsa": ORDEM_BOLSA, "ano": anos},
        labels={
            "ano": "Ano do vestibular",
            "n_aprovados": "Aprovados",
            "categoria_bolsa": "Situação de bolsa",
        },
    )
    fig.update_traces(
        hovertemplate=(
            "<b>Ano:</b> %{x}<br>"
            "<b>%{fullData.name}</b><br>"
            "<b>Aprovados:</b> %{y}<extra></extra>"
        )
    )
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=anos)
    fig.update_layout(legend_title_text="")
    return fig


def _preparar_para_exibicao(dados):
    """Copia o DataFrame com `ano` como texto, só para st.dataframe, evita
    o separador de milhar que o Streamlit aplica a colunas numéricas."""
    dados_exibicao = dados.copy()
    dados_exibicao["ano"] = dados_exibicao["ano"].astype(str)
    return dados_exibicao


def renderizar() -> None:
    """Renderiza a taxa de aprovação dos matriculados e o recorte com/sem bolsa."""
    st.subheader("Taxa de aprovação dos matriculados por ano")

    dados_taxa = carregar_taxa_aprovacao_por_ano()

    st.caption(
        "Dos alunos matriculados em cada ano, o percentual que foi aprovado no "
        "vestibular **do mesmo ano** (matrícula e aprovação no ano X). O "
        "denominador vem de `matriculas` (amostra) e o numerador é conferido "
        "contra `aprovacoes` (base completa), por isso a não-aprovação é real, "
        "não dado faltando. O rótulo de cada barra mostra `aprovados/matriculados`."
    )
    st.plotly_chart(
        _grafico_taxa_aprovacao(dados_taxa), width="stretch", key="taxa_aprovacao_grafico"
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(
            _preparar_para_exibicao(dados_taxa), hide_index=True, key="taxa_aprovacao_tabela"
        )

    st.divider()

    st.subheader("Aprovados com bolsa ou sem bolsa, por ano")

    dados_bolsa = carregar_aprovados_por_bolsa()

    st.caption(
        """Entre os alunos aprovados no vestibular, quantos passaram **com bolsa**
        (integral ou parcial), **sem bolsa**, ou sem essa informação registrada,
        em cada ano. Serve para ver se a quantidade de aprovados com bolsa
        aumentou ou caiu ao longo do tempo frente aos sem bolsa. Calculado só a
        partir de `aprovacoes`, a base completa do desafio."""
    )
    st.plotly_chart(
        _grafico_aprovados_por_bolsa(dados_bolsa), width="stretch", key="aprovados_bolsa_grafico"
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(
            _preparar_para_exibicao(dados_bolsa), hide_index=True, key="aprovados_bolsa_tabela"
        )
