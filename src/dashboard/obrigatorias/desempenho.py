"""Pergunta obrigatória 3: desempenho por matéria (simulado) e por curso (vestibular)."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.dados import (
    carregar_aprovacao_por_faixa_simulado,
    carregar_desempenho_por_curso_aprovado,
    carregar_desempenho_por_materia,
    carregar_desempenho_por_modalidade,
    carregar_simulado_vs_vestibular,
)

CORES_MODALIDADE = {"Presencial": "#4C78A8", "Online": "#72B7B2", "Híbrido": "#B3B3B3"}

COR_BARRA = "#4C78A8"


def _grafico_desempenho_materia(dados) -> go.Figure:
    """Monta o gráfico de barras da nota média de simulado por matéria.

    A mediana e os acertos médios entram no hover, junto do número de
    resultados, o N e a estatística robusta ficam à vista.
    """
    dados = dados.copy()

    fig = px.bar(
        dados,
        x="nome_materia",
        y="nota_media",
        text="nota_media",
        custom_data=["n_resultados", "acertos_medio", "nota_mediana"],
        labels={"nome_materia": "Matéria", "nota_media": "Nota média de simulado"},
    )
    fig.update_traces(
        texttemplate="%{y:.1f}",
        textposition="outside",
        marker_color=COR_BARRA,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<b>Nota média:</b> %{y:.1f}<br>"
            "<b>Nota mediana:</b> %{customdata[2]:.1f}<br>"
            "<b>Acertos médios:</b> %{customdata[1]:.1f}<br>"
            "<b>Resultados:</b> %{customdata[0]}<extra></extra>"
        ),
    )
    fig.update_layout(yaxis_range=[0, 100])
    return fig


def _grafico_aprovacao_por_faixa_simulado(dados) -> go.Figure:
    """Monta o gráfico de barras da taxa de aprovação por faixa de nota de simulado."""
    dados = dados.copy()
    dados["faixa_nota"] = dados["faixa_nota"].astype(str)

    fig = px.bar(
        dados,
        x="faixa_nota",
        y="taxa_aprovacao",
        text="taxa_aprovacao",
        custom_data=["aprovados", "n_alunos"],
        labels={"faixa_nota": "Faixa de nota de simulado", "taxa_aprovacao": "Taxa de aprovação (%)"},
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        marker_color=COR_BARRA,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<b>Taxa de aprovação:</b> %{y:.1f}%<br>"
            "<b>Aprovados:</b> %{customdata[0]} de %{customdata[1]}<extra></extra>"
        ),
    )
    fig.update_layout(yaxis_range=[0, 100])
    return fig


def _grafico_simulado_vs_vestibular(dados) -> go.Figure:
    """Monta o scatter de nota de simulado x nota do vestibular dos aprovados.

    A linha diagonal tracejada marca onde as duas notas seriam iguais.
    Pontos acima dela são alunos que foram melhor no vestibular.
    """
    fig = px.scatter(
        dados,
        x="nota_simulado",
        y="nota_vestibular_norm",
        custom_data=["nota_vestibular", "diferenca"],
        labels={
            "nota_simulado": "Nota de simulado (0-100)",
            "nota_vestibular_norm": "Nota de vestibular (normalizada 0-100)",
        },
    )
    fig.update_traces(
        marker=dict(color="#4C78A8", size=9, opacity=0.75),
        hovertemplate=(
            "<b>Simulado:</b> %{x:.1f}<br>"
            "<b>Vestibular:</b> %{customdata[0]:.1f} (norm. %{y:.1f})<br>"
            "<b>Diferença:</b> %{customdata[1]:+.1f}<extra></extra>"
        ),
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="#B3B3B3", dash="dash"))
    fig.add_annotation(
        x=22, y=92, text="acima da linha = melhor no vestibular",
        showarrow=False, font=dict(color="#888"),
    )
    fig.update_layout(xaxis_range=[0, 100], yaxis_range=[0, 100])
    return fig


def _grafico_desempenho_curso(dados) -> go.Figure:
    """Monta o gráfico de barras horizontais da nota final média por curso aprovado."""
    dados = dados.copy().sort_values("nota_media")

    fig = px.bar(
        dados,
        x="nota_media",
        y="curso_aprovado",
        orientation="h",
        text="nota_media",
        custom_data=["n_aprovados"],
        labels={
            "curso_aprovado": "Curso da universidade",
            "nota_media": "Nota média final do vestibular",
        },
    )
    fig.update_traces(
        texttemplate="%{x:.1f}",
        textposition="outside",
        marker_color=COR_BARRA,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "<b>Nota média:</b> %{x:.1f}<br>"
            "<b>Aprovados:</b> %{customdata[0]}<extra></extra>"
        ),
    )
    fig.update_layout(xaxis_range=[0, dados["nota_media"].max() * 1.12], height=520)
    return fig


def _grafico_desempenho_modalidade(dados) -> go.Figure:
    """Monta o gráfico de barras da taxa de aprovação por modalidade de ensino."""
    dados = dados.copy()

    fig = px.bar(
        dados,
        x="modalidade",
        y="taxa_aprovacao",
        color="modalidade",
        text="taxa_aprovacao",
        color_discrete_map=CORES_MODALIDADE,
        custom_data=["aprovados", "matriculas_ano"],
        labels={"modalidade": "Modalidade", "taxa_aprovacao": "Taxa de aprovação (%)"},
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<b>Taxa de aprovação:</b> %{y:.1f}%<br>"
            "<b>Aprovados:</b> %{customdata[0]}<br>"
            "<b>Matrículas-ano:</b> %{customdata[1]}<extra></extra>"
        ),
    )
    fig.update_layout(yaxis_range=[0, 100], showlegend=False)
    return fig


def renderizar() -> None:
    """Renderiza o desempenho por matéria, por curso e por modalidade de ensino."""
    st.subheader("Nota de simulado x nota do vestibular (aprovados)")

    dados_sv = carregar_simulado_vs_vestibular()

    st.caption(
        "Cada ponto é um aluno aprovado. O eixo X é a nota média de simulado "
        "(0-100) e o eixo Y é a nota do vestibular na mesma escala 0-100 (dividida "
        "por 10, já que o vestibular vai de cerca de 0 a 1000). A linha tracejada "
        "diagonal marca onde a nota de simulado seria igual à do vestibular. Quem "
        "está acima dela foi melhor no vestibular do que no simulado. Simulado e "
        "vestibular são sempre do mesmo ano."
    )
    st.plotly_chart(
        _grafico_simulado_vs_vestibular(dados_sv),
        width="stretch",
        key="simulado_vs_vestibular_grafico",
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(dados_sv, hide_index=True, key="simulado_vs_vestibular_tabela")

    st.divider()

    st.subheader("Desempenho por matéria (notas de simulado)")

    dados_mat = carregar_desempenho_por_materia()

    st.caption(
        "Nota média nos simulados **finalizados** de cada matéria (fonte: "
        "`resultados_sim` ligada a `simulados`). Notas acima de 100 são capadas no "
        "limite da escala (não descartadas). O hover traz também a mediana, os "
        "acertos médios e o número de resultados por matéria."
    )
    st.plotly_chart(
        _grafico_desempenho_materia(dados_mat), width="stretch", key="desempenho_materia_grafico"
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(dados_mat, hide_index=True, key="desempenho_materia_tabela")

    st.divider()

    st.subheader("Nota de simulado x aprovação")

    dados_faixa = carregar_aprovacao_por_faixa_simulado()

    st.caption(
        "Taxa de aprovação dos alunos por faixa de nota média de simulado, para "
        "ver se ir melhor nos simulados está associado a passar no vestibular. "
        "Considera todos os alunos com simulado finalizado (matemática/física) e "
        "confere a aprovação contra `aprovacoes` (base completa). O hover mostra o "
        "N de cada faixa."
    )
    st.plotly_chart(
        _grafico_aprovacao_por_faixa_simulado(dados_faixa),
        width="stretch",
        key="aprovacao_faixa_simulado_grafico",
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(dados_faixa, hide_index=True, key="aprovacao_faixa_simulado_tabela")

    st.divider()

    st.subheader("Desempenho por curso (nota final do vestibular)")

    dados_curso = carregar_desempenho_por_curso_aprovado()

    st.caption(
        "Nota final média de vestibular por curso da universidade em que os alunos "
        "foram aprovados (fonte: `aprovacoes`, base completa). Mede o resultado no "
        "vestibular por curso pretendido, não o domínio de disciplina no cursinho. "
        "Passe o mouse para ver o número de aprovados por curso."
    )
    st.plotly_chart(
        _grafico_desempenho_curso(dados_curso), width="stretch", key="desempenho_curso_grafico"
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(dados_curso, hide_index=True, key="desempenho_curso_tabela")

    st.divider()

    st.header("Análises extras que considero importantes")
    st.caption(
        "Recortes complementares de desempenho que não estavam no enunciado, mas "
        "que ajudam a entender melhor a base."
    )

    st.subheader("Desempenho por modalidade de ensino")

    dados_modalidade = carregar_desempenho_por_modalidade()

    st.caption(
        "Taxa de aprovação dos matriculados por modalidade da turma (Presencial, "
        "Online, Híbrido), ligando a matrícula à oferta para pegar a modalidade e "
        "conferindo a aprovação no mesmo ano contra `aprovacoes`. Um aluno "
        "matriculado em mais de uma modalidade no ano conta em cada uma. Passe o "
        "mouse para ver o N de cada barra."
    )
    st.plotly_chart(
        _grafico_desempenho_modalidade(dados_modalidade),
        width="stretch",
        key="desempenho_modalidade_grafico",
    )

    with st.expander("Ver dados por trás do gráfico"):
        st.dataframe(dados_modalidade, hide_index=True, key="desempenho_modalidade_tabela")
