"""Pergunta 1: evolução da taxa de aprovação ao longo dos anos."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, tema

QUERY_PRINCIPAL = "p1_taxa_aprovacao_por_ano"


def grafico_taxa_por_ano(base: pd.DataFrame) -> go.Figure:
    """Linha da taxa de aprovação por ano, com a média do período.

    Args:
        base: uma linha por ano.

    Returns:
        A figura montada.
    """
    fig = go.Figure()

    media = base.aprovados.sum() / base.matriculados.sum() * 100
    fig.add_hline(
        y=media,
        line=dict(color=tema.TINTA_MUTED, width=1),
        # Rótulo curto e deslocado para baixo, no canto esquerdo: é a única área
        # vazia do gráfico. Texto longo ou centralizado cruza o traço da série,
        # e acima da linha colide com o rótulo do ponto de 2021.
        annotation_text=f"média {media:.1f}%".replace(".", ","),
        annotation_position="bottom left",
        annotation_yshift=-14,
        annotation_font=dict(family=tema.FONTE, size=12, color=tema.TINTA_MUTED),
    )

    fig.add_trace(
        go.Scatter(
            x=base.ano,
            y=base.taxa_aprovacao,
            mode="lines+markers",
            line=dict(color=tema.CATEGORICA[0], width=tema.ESPESSURA_LINHA,
                      shape="linear"),
            marker=dict(
                color=tema.CATEGORICA[0],
                size=tema.TAMANHO_MARCADOR,
                line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL),
            ),
            customdata=base[["matriculados", "aprovados"]],
            hovertemplate=(
                "<b>%{x}</b><br>taxa de aprovação: %{y:.1f}%<br>"
                "%{customdata[1]} aprovados de %{customdata[0]} matriculados"
                "<extra></extra>"
            ),
        )
    )

    destaques = {
        int(base.loc[base.taxa_aprovacao.idxmax(), "ano"]),
        int(base.loc[base.taxa_aprovacao.idxmin(), "ano"]),
        int(base.ano.iloc[-1]),
    }
    for _, linha in base[base.ano.isin(destaques)].iterrows():
        tema.anotar_valor(
            fig,
            linha.ano,
            linha.taxa_aprovacao,
            f"{linha.taxa_aprovacao:.1f}%".replace(".", ","),
            deslocamento_y=16,
        )

    # Sem título de eixo: o sufixo % nos ticks e o título do gráfico já dizem o
    # que está plotado, e o espaço à esquerda fica para os rótulos.
    tema.aplicar_layout(fig, altura=360)
    fig.update_yaxes(range=[0, 50], dtick=10, ticksuffix="%")
    fig.update_xaxes(tickmode="array", tickvals=base.ano.tolist())
    return fig


def grafico_matriculados_e_aprovados(base: pd.DataFrame) -> go.Figure:
    """Colunas empilhadas de aprovados e não aprovados por ano.

    Args:
        base: uma linha por ano.

    Returns:
        A figura montada.
    """
    fig = go.Figure()
    for nome, coluna, cor in (
        ("Aprovados", "aprovados", tema.CATEGORICA[0]),
        ("Não aprovados", "nao_aprovados", tema.DE_ENFASE),
    ):
        fig.add_trace(
            go.Bar(
                name=nome,
                x=base.ano,
                y=base[coluna],
                width=0.25,
                marker=dict(
                    color=cor,
                    line=dict(color=tema.SUPERFICIE, width=tema.GAP_SUPERFICIE / 2),
                ),
                hovertemplate=f"<b>%{{x}}</b><br>{nome.lower()}: %{{y}}<extra></extra>",
            )
        )

    # Total de matriculados na ponta da coluna, em tinta de texto.
    for _, linha in base.iterrows():
        tema.anotar_valor(
            fig, linha.ano, linha.matriculados, f"{int(linha.matriculados)}",
            deslocamento_y=14, cor=tema.TINTA_SECUNDARIA,
        )

    tema.aplicar_layout(fig, altura=360, legenda=True)
    fig.update_layout(barmode="stack", bargap=0.2)
    fig.update_yaxes(range=[0, base.matriculados.max() * 1.18])
    fig.update_xaxes(tickmode="array", tickvals=base.ano.tolist())
    return fig


def _movimentos(base: pd.DataFrame) -> str:
    """Monta o comentário dos movimentos a partir dos dados.

    Args:
        base: uma linha por ano.

    Returns:
        O texto em markdown.
    """
    primeiro, ultimo = base.iloc[0], base.iloc[-1]
    melhor = base.loc[base.taxa_aprovacao.idxmax()]
    pior = base.loc[base.taxa_aprovacao.idxmin()]
    amplitude = melhor.taxa_aprovacao - pior.taxa_aprovacao
    media = base.aprovados.sum() / base.matriculados.sum() * 100
    cresc_matric = (ultimo.matriculados / primeiro.matriculados - 1) * 100
    cresc_aprov = (ultimo.aprovados / primeiro.aprovados - 1) * 100
    sinais = (base.variacao_pp.dropna() > 0).astype(int)
    trocas = int(sinais.diff().abs().sum())        # trocas de sinal entre intervalos
    intervalos = len(sinais)
    variacoes = ", ".join(
        f"{v:+.1f} pp".replace(".", ",") for v in base.variacao_pp.dropna()
    )

    def pct(valor: float, casas: int = 1) -> str:
        return f"{valor:.{casas}f}".replace(".", ",")

    return f"""
**A taxa não tem tendência.** O maior valor é {pct(melhor.taxa_aprovacao)}% em
{int(melhor.ano)} e o menor é {pct(pior.taxa_aprovacao)}% em {int(pior.ano)}, uma
diferença de {pct(amplitude)} pontos percentuais em torno da média de {pct(media)}%.
De um ano para o outro a taxa alterna entre subir e cair ({trocas} trocas de sinal em
{intervalos} intervalos: {variacoes}), sem seguir direção nenhuma. Esse vai e vem é o
que se espera de variação normal entre turmas, e não de um preparo que melhorou ou
piorou.

**O que de fato cresceu foi a operação.** Os matriculados por ano subiram de
{int(primeiro.matriculados)} para {int(ultimo.matriculados)}, um aumento de
{pct(cresc_matric)}%. Os aprovados subiram de {int(primeiro.aprovados)} para
{int(ultimo.aprovados)}, ou {pct(cresc_aprov)}%. Como os dois crescem quase no mesmo
ritmo, a taxa fica parada. Em outras palavras, o cursinho vem formando mais aprovados
em número absoluto, mas converte sempre a mesma proporção de alunos.
""".strip()


def renderizar() -> None:
    """Renderiza a página da pergunta 1."""
    st.subheader("1. Qual foi a evolução da taxa de aprovação ao longo dos anos?")
    st.caption(
        "Dos alunos matriculados no cursinho em cada ano, quantos passaram no "
        "vestibular daquele mesmo ano."
    )

    base = dados.consultar(QUERY_PRINCIPAL)

    media = base.aprovados.sum() / base.matriculados.sum() * 100
    melhor = base.loc[base.taxa_aprovacao.idxmax()]
    pior = base.loc[base.taxa_aprovacao.idxmin()]
    ultimo, primeiro = base.iloc[-1], base.iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Taxa média do período", f"{media:.1f}%".replace(".", ","),
                help="Total de aprovados dividido pelo total de matriculados nos 5 anos.")
    col2.metric(f"Taxa em {int(ultimo.ano)}", f"{ultimo.taxa_aprovacao:.1f}%".replace(".", ","),
                delta=f"{ultimo.variacao_pp:+.1f} pp vs {int(ultimo.ano) - 1}".replace(".", ","))
    col3.metric("Amplitude entre anos", f"{melhor.taxa_aprovacao - pior.taxa_aprovacao:.1f} pp".replace(".", ","),
                help=f"Entre {pior.taxa_aprovacao:.1f}% em {int(pior.ano)} e "
                     f"{melhor.taxa_aprovacao:.1f}% em {int(melhor.ano)}.")
    col4.metric(f"Matriculados em {int(ultimo.ano)}", f"{int(ultimo.matriculados)}",
                delta=f"{int(ultimo.matriculados - primeiro.matriculados):+d} vs {int(primeiro.ano)}")

    st.divider()

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Taxa de aprovação por ano**")
        st.caption("% dos matriculados aprovados no vestibular do mesmo ano")
        st.plotly_chart(grafico_taxa_por_ano(base), use_container_width=True,
                        config={"displayModeBar": False})
    with direita:
        st.markdown("**Matriculados e aprovados por ano**")
        st.caption("total de matriculados, separado entre aprovados e não aprovados")
        st.plotly_chart(grafico_matriculados_e_aprovados(base), use_container_width=True,
                        config={"displayModeBar": False})

    with st.expander("Ver os números em tabela"):
        st.dataframe(
            base.rename(columns={
                "ano": "Ano", "matriculados": "Matriculados", "aprovados": "Aprovados",
                "nao_aprovados": "Não aprovados", "taxa_aprovacao": "Taxa (%)",
                "variacao_pp": "Variação (pp)",
            }),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
    st.markdown("#### Principais movimentos observados")
    st.markdown(_movimentos(base))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        st.caption(f"`src/dashboard/querys/{QUERY_PRINCIPAL}.sql`")
        st.code(dados.ler_sql(QUERY_PRINCIPAL), language="sql")
