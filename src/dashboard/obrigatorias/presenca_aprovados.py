"""Pergunta obrigatória 2: relação entre presença nas aulas e aprovação no vestibular."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.dados import carregar_presenca_aprovacao

CORES_SITUACAO = {"Aprovado": "#4C78A8", "Não aprovado": "#E45756"}
ORDEM_SITUACAO = ["Aprovado", "Não aprovado"]


def _grafico_presenca_aprovacao(dados) -> go.Figure:
    """Monta o gráfico de barras agrupadas da taxa de presença por ano e situação.

    Para cada ano, uma barra de aprovados e outra de não aprovados. O hover
    traz o número de alunos e de registros de presença que sustentam a
    taxa, o N fica explícito, já que a amostra é pequena.
    """
    dados = dados.copy()
    dados["ano"] = dados["ano"].astype(str)
    anos = sorted(dados["ano"].unique())

    fig = px.bar(
        dados,
        x="ano",
        y="taxa_presenca",
        color="situacao",
        barmode="group",
        text="taxa_presenca",
        color_discrete_map=CORES_SITUACAO,
        category_orders={"situacao": ORDEM_SITUACAO, "ano": anos},
        custom_data=["situacao", "n_alunos", "total_aulas"],
        labels={"ano": "Ano", "taxa_presenca": "Taxa de presença (%)", "situacao": "Situação"},
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        hovertemplate=(
            "<b>Ano:</b> %{x}<br>"
            "<b>%{customdata[0]}</b><br>"
            "<b>Taxa de presença:</b> %{y:.1f}%<br>"
            "<b>Alunos:</b> %{customdata[1]}<br>"
            "<b>Registros de presença:</b> %{customdata[2]}<extra></extra>"
        ),
    )
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=anos)
    fig.update_layout(yaxis_range=[0, 100], legend_title_text="")
    return fig


def renderizar() -> None:
    """Renderiza a comparação de presença entre alunos aprovados e não aprovados."""
    st.subheader("Presença nas aulas: aprovados x não aprovados")

    dados_presenca = carregar_presenca_aprovacao()

    st.caption(
        "Taxa de presença dos alunos por ano, separando quem foi aprovado no "
        "vestibular **daquele mesmo ano** de quem não foi. A presença é amarrada ao "
        "ano da aula (via `aula_id` → `aulas.ano`), então só é comparada com a "
        "aprovação do mesmo ano. Considera **apenas os alunos que têm presença "
        "registrada** em `presencas_aulas` (amostra curta, que hoje só cobre aulas "
        "de 2021), e a aprovação é conferida contra `aprovacoes`, a base completa. "
        "Passe o mouse para ver o número de alunos por trás de cada barra."
    )
    st.plotly_chart(
        _grafico_presenca_aprovacao(dados_presenca),
        width="stretch",
        key="presenca_aprovacao_grafico",
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(dados_presenca, hide_index=True, key="presenca_aprovacao_tabela")
