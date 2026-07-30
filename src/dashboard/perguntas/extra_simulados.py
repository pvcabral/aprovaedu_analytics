"""Análise extra: desempenho nos simulados por dispositivo e unidade de aplicação."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, graficos, tema

QUERY_DISPOSITIVO = "ex_simulados_por_dispositivo"
QUERY_UNIDADE = "ex_simulados_por_unidade"
QUERY_TENTATIVAS = "ex_simulados_nota_por_tentativas"


def grafico_nota_por_categoria(base: pd.DataFrame, coluna: str) -> go.Figure:
    """Faixa do percentil 10 ao 90 da nota, com a mediana marcada.

    Args:
        base: uma linha por categoria.
        coluna: coluna com o nome da categoria.

    Returns:
        A figura montada.
    """
    return graficos.faixa_com_mediana(
        base,
        coluna_categoria=coluna,
        coluna_mediana="nota_mediana",
        coluna_inferior="nota_percentil_10",
        coluna_superior="nota_percentil_90",
        titulo_x="nota do simulado (0 a 100)",
        faixa_x=(0, 100),
        altura=340,
        margem_esquerda=120,
        hover_extra=["resultados", "nota_desvio"],
    )


def grafico_tentativas_por_categoria(base: pd.DataFrame, coluna: str) -> go.Figure:
    """Média de tentativas por categoria, no eixo de 1 a 3.

    Args:
        base: uma linha por categoria.
        coluna: coluna com o nome da categoria.

    Returns:
        A figura montada.
    """
    ordenado = base.sort_values("tentativas_media")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=ordenado.tentativas_media,
            y=ordenado[coluna],
            orientation="h",
            width=0.4,
            marker=dict(color=tema.CATEGORICA[0]),
            text=ordenado.tentativas_media.map(lambda valor: f"{valor:.2f}".replace(".", ",")),
            textposition="outside",
            textfont=dict(family=tema.FONTE, size=12, color=tema.TINTA_SECUNDARIA),
            customdata=ordenado[["sem_tentativa_registrada", "resultados"]],
            hovertemplate=(
                "<b>%{y}</b><br>tentativas em média: %{x:.2f}<br>"
                "sem tentativa registrada: %{customdata[0]} de %{customdata[1]}"
                "<extra></extra>"
            ),
        )
    )
    tema.aplicar_layout(fig, altura=340, titulo_x="tentativas por resultado",
                        margem_esquerda=120)
    fig.update_xaxes(range=[1, 3], dtick=0.5, showgrid=True, gridcolor=tema.GRADE)
    fig.update_yaxes(showgrid=False, type="category")
    return fig


def grafico_nota_por_tentativas(tentativas: pd.DataFrame) -> go.Figure:
    """Nota mediana conforme o número de tentativas.

    Args:
        tentativas: uma linha por número de tentativas.

    Returns:
        A figura montada.
    """
    base = tentativas.sort_values("tentativas")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=base.tentativas.astype(int).astype(str),
            y=base.nota_mediana,
            width=0.3,
            marker=dict(color=tema.CATEGORICA[0]),
            text=base.nota_mediana.map(lambda valor: f"{valor:.1f}".replace(".", ",")),
            textposition="outside",
            textfont=dict(family=tema.FONTE, size=12, color=tema.TINTA_SECUNDARIA),
            customdata=base[["resultados", "nota_desvio", "tempo_medio_min"]],
            hovertemplate=(
                "<b>%{x} tentativa(s)</b><br>nota mediana: %{y:.1f}<br>"
                "desvio: %{customdata[1]:.1f}<br>%{customdata[0]} resultados<br>"
                "tempo médio: %{customdata[2]:.0f} min<extra></extra>"
            ),
        )
    )
    tema.aplicar_layout(fig, altura=340, titulo_x="tentativas até concluir")
    fig.update_yaxes(range=[0, 100], dtick=20,
                     title=dict(text="nota mediana",
                                font=dict(color=tema.TINTA_MUTED, size=12)))
    return fig


def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto(dispositivo: pd.DataFrame, unidade: pd.DataFrame,
           tentativas: pd.DataFrame) -> str:
    """Monta o texto da análise.

    Returns:
        O texto em markdown.
    """
    faixa_disp = dispositivo.nota_mediana.max() - dispositivo.nota_mediana.min()
    faixa_unid = unidade.nota_mediana.max() - unidade.nota_mediana.min()
    faixa_tent = dispositivo.tentativas_media.max() - dispositivo.tentativas_media.min()
    sem_registro = int(dispositivo.sem_tentativa_registrada.sum())
    total = int(dispositivo.resultados.sum())
    variacao_nota_tent = tentativas.nota_mediana.max() - tentativas.nota_mediana.min()

    return f"""
**Dispositivo e local de aplicação não mudam o resultado.** A nota mediana varia
{_num(faixa_disp)} ponto entre os cinco dispositivos e {_num(faixa_unid)} ponto entre as
cinco unidades, numa escala de 0 a 100. O espalhamento também é igual: a faixa que cobre
80% dos alunos tem praticamente o mesmo comprimento em todos. Fazer o simulado no
celular, no desktop, no tablet ou no papel dá no mesmo, e o mesmo vale para fazer online
ou em qualquer das três unidades físicas.

**Tentativas também não distinguem.** A média fica entre
{_num(dispositivo.tentativas_media.min(), 2)} e
{_num(dispositivo.tentativas_media.max(), 2)} tentativas por resultado, uma variação de
{_num(faixa_tent, 2)}. E mais importante: tentativa não compra nota. Quem concluiu na
primeira tem mediana de {_num(tentativas.iloc[0].nota_mediana)}, e quem precisou de três
tem {_num(tentativas.iloc[-1].nota_mediana)}, {_num(variacao_nota_tent)} ponto de
diferença. Repetir o simulado não melhora o desempenho, então tentativas mede atrito, e
não esforço que rende.

**Uma ressalva sobre o campo de tentativas.** Na origem ele só tem os valores 1, 2 e 3,
além de nulos, e o tratamento preencheu os nulos com 0. São {sem_registro} de {total}
resultados sem tentativa registrada, {_num(100 * sem_registro / total)}% do total. As
consultas desta página convertem o 0 de volta para nulo, senão a média de tentativas
viria puxada para baixo por registros que nunca foram medidos. Vale corrigir isso no
tratamento na próxima carga, do mesmo jeito que já foi feito com `acertos` e `atraso_min`.
"""


def renderizar() -> None:
    """Renderiza a página de aplicação dos simulados."""
    st.subheader("Desempenho nos simulados por dispositivo e unidade")
    st.caption(
        "Quatro indicadores lado a lado, em vez de um índice: nota mediana, "
        "espalhamento, tentativas e conclusão. Juntar nota e tentativas num número só "
        "exigiria decidir quanto vale cada um, e esse peso não sai dos dados."
    )

    dispositivo = dados.consultar(QUERY_DISPOSITIVO)
    unidade = dados.consultar(QUERY_UNIDADE)
    tentativas = dados.consultar(QUERY_TENTATIVAS)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Variação da nota entre dispositivos",
        f"{dispositivo.nota_mediana.max() - dispositivo.nota_mediana.min():.1f} ponto".replace(".", ","),
        help="Entre o dispositivo de maior e o de menor nota mediana, numa escala de 0 a 100.",
    )
    col2.metric(
        "Variação da nota entre unidades",
        f"{unidade.nota_mediana.max() - unidade.nota_mediana.min():.1f} ponto".replace(".", ","),
        help="Entre a unidade de aplicação de maior e a de menor nota mediana.",
    )
    col3.metric(
        "Tentativas por resultado",
        f"{dispositivo.tentativas_media.mean():.2f}".replace(".", ","),
        help="Média geral. O campo só assume 1, 2 ou 3 na origem.",
    )
    col4.metric(
        "Sem tentativa registrada",
        f"{100 * dispositivo.sem_tentativa_registrada.sum() / dispositivo.resultados.sum():.1f}%".replace(".", ","),
        help="Resultados em que o número de tentativas não foi informado na origem.",
    )

    st.divider()
    st.markdown("### Por dispositivo")

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Nota e espalhamento**")
        st.caption("a barra vai do percentil 10 ao 90 e o ponto é a mediana")
        st.plotly_chart(grafico_nota_por_categoria(dispositivo, "dispositivo"),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Tentativas por resultado**")
        st.caption("eixo de 1 a 3, a faixa que o campo assume na origem")
        st.plotly_chart(grafico_tentativas_por_categoria(dispositivo, "dispositivo"),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("### Por unidade de aplicação")

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Nota e espalhamento**")
        st.caption("mesma leitura do gráfico de dispositivo, por local de aplicação")
        st.plotly_chart(grafico_nota_por_categoria(unidade, "unidade_aplicacao"),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Tentativas por resultado**")
        st.caption("eixo de 1 a 3, a faixa que o campo assume na origem")
        st.plotly_chart(grafico_tentativas_por_categoria(unidade, "unidade_aplicacao"),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("### Tentativa rende nota?")
    st.caption(
        "se repetir o simulado melhorasse o desempenho, a nota subiria da esquerda "
        "para a direita"
    )
    st.plotly_chart(grafico_nota_por_tentativas(tentativas),
                    use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver os números em tabela"):
        for titulo, base in (("Por dispositivo", dispositivo),
                             ("Por unidade de aplicação", unidade)):
            st.markdown(f"**{titulo}**")
            st.dataframe(
                base.rename(columns={
                    "dispositivo": "Dispositivo", "unidade_aplicacao": "Unidade",
                    "resultados": "Resultados", "nota_mediana": "Nota mediana",
                    "nota_desvio": "Desvio padrão",
                    "nota_percentil_10": "Percentil 10",
                    "nota_percentil_90": "Percentil 90",
                    "tentativas_media": "Tentativas (média)",
                    "sem_tentativa_registrada": "Sem tentativa registrada",
                    "pct_concluido": "Concluídos (%)",
                }),
                hide_index=True, use_container_width=True,
            )
        st.markdown("**Nota por número de tentativas**")
        st.dataframe(
            tentativas.rename(columns={
                "tentativas": "Tentativas", "resultados": "Resultados",
                "nota_mediana": "Nota mediana", "nota_desvio": "Desvio padrão",
                "tempo_medio_min": "Tempo médio (min)",
            }),
            hide_index=True, use_container_width=True,
        )

    st.divider()
    st.markdown("#### O que os dados mostram")
    st.markdown(_texto(dispositivo, unidade, tentativas))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        for nome in (QUERY_DISPOSITIVO, QUERY_UNIDADE, QUERY_TENTATIVAS):
            st.caption(f"`src/dashboard/querys/{nome}.sql`")
            st.code(dados.ler_sql(nome), language="sql")
