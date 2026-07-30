"""Pergunta 2: existe relação entre presença nas aulas e aprovação no vestibular?"""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, tema

QUERY_POR_ALUNO = "p2_presenca_por_aluno"
QUERY_POR_FAIXA = "p2_aprovacao_por_faixa_de_presenca"
QUERY_POR_ANO = "p2_presenca_por_ano_e_situacao"
QUERY_ESTATISTICAS = "p2_estatisticas_presenca"

APROVADO, NAO_APROVADO = "Aprovado", "Não aprovado"
COR_APROVADO = tema.CATEGORICA[0]
COR_NAO_APROVADO = tema.CATEGORICA[1]


def grafico_distribuicao_presenca(por_aluno: pd.DataFrame) -> go.Figure:
    """Histograma da presença individual.

    Args:
        por_aluno: uma linha por aluno e ano.

    Returns:
        A figura montada.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=por_aluno.taxa_presenca,
            xbins=dict(start=70, end=100, size=2),
            marker=dict(
                color=COR_APROVADO,
                line=dict(color=tema.SUPERFICIE, width=tema.GAP_SUPERFICIE / 2),
            ),
            hovertemplate="presença entre %{x}<br>%{y} alunos<extra></extra>",
        )
    )

    media = por_aluno.taxa_presenca.mean()
    fig.add_vline(
        x=media,
        line=dict(color=tema.TINTA_MUTED, width=1),
        annotation_text=f"média {media:.1f}%".replace(".", ","),
        annotation_position="top right",
        annotation_font=dict(family=tema.FONTE, size=12, color=tema.TINTA_MUTED),
    )

    tema.aplicar_layout(fig, altura=340, titulo_x="presença do aluno no ano")
    fig.update_xaxes(range=[68, 100], ticksuffix="%", dtick=5)
    fig.update_yaxes(title=dict(text="alunos", font=dict(color=tema.TINTA_MUTED, size=12)))
    return fig


def grafico_aprovacao_por_faixa(por_faixa: pd.DataFrame) -> go.Figure:
    """Barras da taxa de aprovação por faixa de presença, com a média geral.

    Args:
        por_faixa: uma linha por faixa de presença.

    Returns:
        A figura montada.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=por_faixa.faixa_presenca,
            y=por_faixa.taxa_aprovacao,
            width=0.25,
            marker=dict(color=COR_APROVADO),
            customdata=por_faixa[["alunos", "aprovados"]],
            hovertemplate=(
                "<b>%{x}</b><br>taxa de aprovação: %{y:.1f}%<br>"
                "%{customdata[1]} aprovados de %{customdata[0]} alunos<extra></extra>"
            ),
        )
    )

    media = por_faixa.aprovados.sum() / por_faixa.alunos.sum() * 100
    fig.add_hline(
        y=media,
        line=dict(color=tema.TINTA_MUTED, width=1),
        annotation_text=f"média geral {media:.1f}%".replace(".", ","),
        # À direita: à esquerda a anotação colidiria com o rótulo da primeira barra.
        annotation_position="top right",
        annotation_font=dict(family=tema.FONTE, size=12, color=tema.TINTA_MUTED),
    )

    # Valor na tampa de cada coluna: são só 5 barras e o número é a resposta.
    for _, linha in por_faixa.iterrows():
        tema.anotar_valor(
            fig, linha.faixa_presenca, linha.taxa_aprovacao,
            f"{linha.taxa_aprovacao:.1f}%".replace(".", ","), deslocamento_y=14,
        )

    tema.aplicar_layout(fig, altura=340, titulo_x="faixa de presença do aluno")
    fig.update_yaxes(range=[0, 50], dtick=10, ticksuffix="%")
    return fig


def grafico_presenca_por_ano(
    por_ano: pd.DataFrame, faixa_individual: tuple[float, float] | None = None
) -> go.Figure:
    """Presença de aprovados e não aprovados, ano a ano, como halteres.

    Args:
        por_ano: uma linha por ano e situação.
        faixa_individual: (1º quartil, 3º quartil) da presença individual,
            desenhada como faixa de fundo para dar escala à diferença.

    Returns:
        A figura montada.
    """
    largo = por_ano.pivot(index="ano", columns="situacao", values="taxa_presenca")
    largo = largo.sort_index(ascending=False)   # ano mais recente no topo

    fig = go.Figure()

    if faixa_individual:
        inferior, superior = faixa_individual
        # Sem rótulo dentro do gráfico: qualquer posição colide com as marcas de
        # um dos anos. A faixa é explicada na legenda de texto acima do gráfico.
        fig.add_vrect(
            x0=inferior,
            x1=superior,
            fillcolor=tema.GRADE,
            opacity=0.6,
            line_width=0,
            layer="below",
        )

    # Conector primeiro, para as marcas ficarem por cima dele.
    for ano, linha in largo.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[linha[APROVADO], linha[NAO_APROVADO]],
                y=[str(ano), str(ano)],
                mode="lines",
                line=dict(color=tema.LINHA_BASE, width=tema.ESPESSURA_LINHA),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    for situacao, cor in ((APROVADO, COR_APROVADO), (NAO_APROVADO, COR_NAO_APROVADO)):
        dados_grupo = por_ano[por_ano.situacao == situacao].set_index("ano")
        dados_grupo = dados_grupo.reindex(largo.index)
        fig.add_trace(
            go.Scatter(
                name=situacao,
                x=dados_grupo.taxa_presenca,
                y=[str(ano) for ano in largo.index],
                mode="markers",
                marker=dict(
                    color=cor,
                    size=13,
                    line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL),
                ),
                customdata=dados_grupo[["alunos"]],
                hovertemplate=(
                    f"<b>%{{y}} · {situacao}</b><br>presença: %{{x:.1f}}%<br>"
                    "%{customdata[0]} alunos<extra></extra>"
                ),
            )
        )

    tema.aplicar_layout(fig, altura=300, titulo_x="presença média do grupo", legenda=True)
    fig.update_xaxes(range=[70, 100], ticksuffix="%", dtick=5,
                     showgrid=True, gridcolor=tema.GRADE)
    fig.update_yaxes(showgrid=False, type="category")
    return fig


def _intervalo_da_diferenca(estatisticas: pd.DataFrame) -> tuple[float, float, float]:
    """Diferença de presença entre os grupos, com intervalo de 95% por Welch.

    Args:
        estatisticas: uma linha por situação, com `alunos`, `presenca_media` e
            `desvio_padrao`.

    Returns:
        (diferença em pontos percentuais, limite inferior, limite superior).
    """
    grupo = estatisticas.set_index("situacao")
    aprovado, nao_aprovado = grupo.loc[APROVADO], grupo.loc[NAO_APROVADO]

    diferenca = float(aprovado.presenca_media - nao_aprovado.presenca_media)
    erro = math.sqrt(
        float(aprovado.desvio_padrao) ** 2 / int(aprovado.alunos)
        + float(nao_aprovado.desvio_padrao) ** 2 / int(nao_aprovado.alunos)
    )
    return diferenca, diferenca - 1.96 * erro, diferenca + 1.96 * erro


def _conclusao(por_aluno: pd.DataFrame, por_faixa: pd.DataFrame,
               por_ano: pd.DataFrame, estatisticas: pd.DataFrame) -> str:
    """Monta a resposta da pergunta a partir dos dados.

    Returns:
        O texto em markdown.
    """
    diferenca, inferior, superior = _intervalo_da_diferenca(estatisticas)
    grupo = estatisticas.set_index("situacao")
    correlacao = float(estatisticas.correlacao.iloc[0])
    primeira, ultima = por_faixa.iloc[0], por_faixa.iloc[-1]

    largo = por_ano.pivot(index="ano", columns="situacao", values="taxa_presenca")
    anos_invertidos = int((largo[NAO_APROVADO] > largo[APROVADO]).sum())
    q1 = por_aluno.taxa_presenca.quantile(0.25)
    q3 = por_aluno.taxa_presenca.quantile(0.75)

    def num(valor: float, casas: int = 1) -> str:
        return f"{valor:.{casas}f}".replace(".", ",")

    def inteiro(valor: int) -> str:
        return f"{valor:,}".replace(",", ".")

    return f"""
**Não há relação detectável.** A presença média de quem passou é
{num(grupo.loc[APROVADO, "presenca_media"])}% e de quem não passou é
{num(grupo.loc[NAO_APROVADO, "presenca_media"])}%, uma diferença de {num(diferenca)}
ponto percentual. Com {inteiro(len(por_aluno))} casos, a margem de erro dessa
diferença vai de {num(inferior)} a {num(superior)} ponto, ou seja, ela inclui o zero.
Isso significa que a diferença observada não se distingue de nenhuma diferença. A
correlação entre presença e aprovação é de {num(correlacao, 3)}, praticamente zero. E
em {anos_invertidos} dos {largo.shape[0]} anos quem não passou teve presença maior do
que quem passou.

**Frequentar mais não aumenta a chance de passar.** Separando os alunos por faixa de
presença, a taxa de aprovação fica entre {num(por_faixa.taxa_aprovacao.min())}% e
{num(por_faixa.taxa_aprovacao.max())}%, sem seguir direção nenhuma. A faixa de maior
presença ({ultima.faixa_presenca.lower()}) tem taxa de {num(ultima.taxa_aprovacao)}%,
abaixo da faixa de menor presença ({primeira.faixa_presenca.lower()}, com
{num(primeira.taxa_aprovacao)}%). Se a presença explicasse a aprovação, essa escada
subiria da esquerda para a direita.

**Por que isso não significa "faltar não custa".** A presença varia pouco nesta base:
vai de {num(por_aluno.taxa_presenca.min())}% a {num(por_aluno.taxa_presenca.max())}%,
e metade dos alunos está entre {num(q1)}% e {num(q3)}%. Não existe aqui o aluno de
presença baixa que serviria de contraprova, então o que foi medido é o efeito de
frequentar {num(q1)}% contra {num(q3)}% das aulas, e não o de faltar muito.
""".strip()


def renderizar() -> None:
    """Renderiza a página da pergunta 2."""
    st.subheader("2. Existe relação entre presença nas aulas e aprovação no vestibular?")
    st.caption(
        "Presença é o comparecimento do aluno às aulas registradas do ano: contam "
        "as aulas em que ele esteve presente ou chegou atrasado. Falta justificada "
        "não conta como comparecimento."
    )

    por_aluno = dados.consultar(QUERY_POR_ALUNO)
    por_faixa = dados.consultar(QUERY_POR_FAIXA)
    por_ano = dados.consultar(QUERY_POR_ANO)
    estatisticas = dados.consultar(QUERY_ESTATISTICAS)

    grupo = estatisticas.set_index("situacao")
    diferenca, inferior, superior = _intervalo_da_diferenca(estatisticas)
    correlacao = float(estatisticas.correlacao.iloc[0])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Presença de quem passou",
        f"{grupo.loc[APROVADO, 'presenca_media']:.1f}%".replace(".", ","),
        help=f"Média entre os {int(grupo.loc[APROVADO, 'alunos'])} alunos aprovados "
             "no vestibular do ano.",
    )
    col2.metric(
        "Presença de quem não passou",
        f"{grupo.loc[NAO_APROVADO, 'presenca_media']:.1f}%".replace(".", ","),
        help=f"Média entre os {int(grupo.loc[NAO_APROVADO, 'alunos'])} alunos sem "
             "aprovação no vestibular do ano.",
    )
    col3.metric(
        "Diferença entre os grupos",
        f"{diferenca:+.1f} pp".replace(".", ","),
        help=(
            f"Margem de erro de 95%: de {inferior:+.1f} a {superior:+.1f} ponto. "
            "Como o intervalo passa pelo zero, a diferença não se distingue de "
            "nenhuma diferença."
        ).replace(".", ",", 2),
    )
    col4.metric(
        "Correlação com a aprovação",
        f"{correlacao:+.3f}".replace(".", ","),
        help=(
            "Correlação entre a presença do aluno e ter passado, de -1 a +1. Perto "
            "de zero, saber a presença não diz nada sobre a chance de passar. O "
            "cálculo e a explicação completa estão em "
            "src/dashboard/querys/p2_estatisticas_presenca.sql."
        ),
    )

    st.divider()

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Como a presença se distribui**")
        st.caption("alunos por faixa de presença, um ponto por aluno e ano")
        st.plotly_chart(grafico_distribuicao_presenca(por_aluno),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Taxa de aprovação por faixa de presença**")
        st.caption("se presença ajudasse, a taxa subiria da esquerda para a direita")
        st.plotly_chart(grafico_aprovacao_por_faixa(por_faixa),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("**Presença de aprovados e não aprovados, ano a ano**")
    quartis = (por_aluno.taxa_presenca.quantile(0.25), por_aluno.taxa_presenca.quantile(0.75))
    st.caption(
        "a distância entre as duas marcas é a diferença entre os grupos · a faixa "
        f"cinza marca onde está a metade central dos alunos "
        f"({quartis[0]:.1f}% a {quartis[1]:.1f}%)".replace(".", ",")
    )
    st.plotly_chart(grafico_presenca_por_ano(por_ano, faixa_individual=quartis),
                    use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver os números em tabela"):
        st.markdown("**Taxa de aprovação por faixa de presença**")
        st.dataframe(
            por_faixa.drop(columns=["faixa_ordem"]).rename(columns={
                "faixa_presenca": "Faixa de presença", "alunos": "Alunos",
                "aprovados": "Aprovados", "taxa_aprovacao": "Taxa de aprovação (%)",
            }),
            hide_index=True, use_container_width=True,
        )
        st.markdown("**Presença por ano e situação**")
        st.dataframe(
            por_ano.rename(columns={
                "ano": "Ano", "situacao": "Situação", "alunos": "Alunos",
                "aulas_registradas": "Aulas registradas",
                "comparecimentos": "Comparecimentos", "taxa_presenca": "Presença (%)",
            }),
            hide_index=True, use_container_width=True,
        )
        st.markdown("**Estatísticas dos dois grupos**")
        st.caption(
            "média, desvio padrão e correlação como saem do banco. É a base dos "
            "números do topo da página."
        )
        st.dataframe(
            estatisticas.rename(columns={
                "situacao": "Situação", "alunos": "Alunos",
                "presenca_media": "Presença média (%)",
                "desvio_padrao": "Desvio padrão (pp)", "correlacao": "Correlação",
            }),
            hide_index=True, use_container_width=True,
        )

    st.divider()
    st.markdown("#### O que os dados mostram")
    st.markdown(_conclusao(por_aluno, por_faixa, por_ano, estatisticas))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        for nome in (QUERY_POR_FAIXA, QUERY_POR_ANO, QUERY_ESTATISTICAS, QUERY_POR_ALUNO):
            st.caption(f"`src/dashboard/querys/{nome}.sql`")
            st.code(dados.ler_sql(nome), language="sql")
