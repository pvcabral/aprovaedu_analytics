"""Análise extra: professores, as matérias que lecionam e o desempenho em cada uma."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, graficos, tema

QUERY_MATERIAS = "ex_professores_materias"
QUERY_DESEMPENHO = "ex_professores_desempenho"


def grafico_declaradas_vs_lecionadas(materias: pd.DataFrame) -> go.Figure:
    """Contagem de professores por número de matérias declaradas.

    Args:
        materias: uma linha por professor.

    Returns:
        A figura montada.
    """
    contagem = (
        materias.groupby("materias_declaradas")
        .agg(professores=("professor_id", "count"),
             media_com_aula=("materias_com_aula", "mean"))
        .reset_index()
    )
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=contagem.materias_declaradas.astype(str),
            y=contagem.professores,
            width=0.35,
            marker=dict(color=tema.CATEGORICA[0]),
            text=contagem.professores,
            textposition="outside",
            textfont=dict(family=tema.FONTE, size=12, color=tema.TINTA_SECUNDARIA),
            customdata=contagem[["media_com_aula"]],
            hovertemplate=(
                "<b>%{x} matéria(s) declarada(s)</b><br>%{y} professores<br>"
                "matérias com aula: %{customdata[0]:.1f}<extra></extra>"
            ),
        )
    )
    tema.aplicar_layout(fig, altura=320, titulo_x="matérias que o professor declara ensinar")
    fig.update_yaxes(range=[0, contagem.professores.max() * 1.25],
                     title=dict(text="professores",
                                font=dict(color=tema.TINTA_MUTED, size=12)))
    return fig


def grafico_nota_por_professor(desempenho: pd.DataFrame) -> go.Figure:
    """Nota dos simulados de cada professor, com intervalo de 95%.

    Args:
        desempenho: uma linha por professor.

    Returns:
        A figura montada.
    """
    base = desempenho.dropna(subset=["nota_media"])
    return graficos.pontos_com_intervalo(
        base,
        coluna_categoria="nome_professor",
        coluna_valor="nota_media",
        coluna_inferior="limite_inferior",
        coluna_superior="limite_superior",
        titulo_x="nota média dos simulados que o professor criou (0 a 100)",
        faixa_x=(50, 80),
        altura=760,
        margem_esquerda=190,
        hover_extra=["materia", "resultados"],
    )


def grafico_presenca_por_professor(desempenho: pd.DataFrame) -> go.Figure:
    """Comparecimento dos alunos nas aulas de cada professor.

    Args:
        desempenho: uma linha por professor.

    Returns:
        A figura montada.
    """
    base = desempenho.dropna(subset=["presenca"]).sort_values("presenca")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=base.presenca,
            y=base.nome_professor,
            mode="markers",
            marker=dict(color=tema.CATEGORICA[0], size=tema.TAMANHO_MARCADOR + 2,
                        line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL)),
            customdata=base[["materia", "aulas"]],
            hovertemplate=(
                "<b>%{y}</b><br>presença: %{x:.1f}%<br>matéria: %{customdata[0]}<br>"
                "%{customdata[1]} aulas<extra></extra>"
            ),
        )
    )
    tema.aplicar_layout(fig, altura=760, titulo_x="comparecimento dos alunos nas aulas",
                        margem_esquerda=190)
    fig.update_xaxes(range=[70, 100], ticksuffix="%", dtick=5,
                     showgrid=True, gridcolor=tema.GRADE)
    fig.update_yaxes(showgrid=False, type="category")
    return fig


def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto(materias: pd.DataFrame, desempenho: pd.DataFrame) -> str:
    """Monta o texto da análise.

    Returns:
        O texto em markdown.
    """
    fora = int(materias.aulas_fora_da_principal.sum())
    total_aulas = int(materias.aulas.sum())
    declaram_mais = int((materias.materias_declaradas > materias.materias_com_aula).sum())
    com_nota = desempenho.dropna(subset=["nota_media"])
    faixa_nota = com_nota.nota_mediana.max() - com_nota.nota_mediana.min()
    com_presenca = desempenho.dropna(subset=["presenca"])
    faixa_presenca = com_presenca.presenca.max() - com_presenca.presenca.min()

    return f"""
**Nenhum professor deu aula fora da própria matéria.** Das {total_aulas} aulas da base,
{fora} foram em matéria diferente da matéria principal do professor. A comparação
pedida, entre desempenho dentro e fora da especialidade, não tem nenhum caso para
comparar.

**Mas o cadastro diz outra coisa.** {declaram_mais} dos {len(materias)} professores
declaram ensinar mais matérias do que lecionam: a coluna `materias_ensina` lista duas ou
três, e todos os {len(materias)} dão aula em exatamente uma. Ou seja, a segunda
habilitação existe no cadastro e nunca é usada na escala. Isso é útil de duas formas:
como aviso de que a informação de habilitação está desatualizada, e como capacidade
ociosa, se de fato esses professores puderem assumir outra matéria.

**Dentro da própria matéria, os professores não se diferenciam.** A nota mediana dos
simulados criados por cada um varia {_num(faixa_nota)} pontos entre o primeiro e o
último, e os intervalos de confiança se sobrepõem quase todos. O comparecimento dos
alunos varia {_num(faixa_presenca)} pontos percentuais entre o professor de maior e o de
menor presença. Nenhum dos dois indicadores separa professor bom de professor ruim nesta
base.
"""


def renderizar() -> None:
    """Renderiza a página de professores."""
    st.subheader("Professores e as matérias que lecionam")
    st.caption(
        "A pergunta de origem era o desempenho de quem dá aula fora da matéria "
        "principal. Na base isso não ocorre, e a página mostra o que existe: a "
        "diferença entre matéria declarada e matéria lecionada, e o desempenho de "
        "cada professor dentro da própria matéria."
    )

    materias = dados.consultar(QUERY_MATERIAS)
    desempenho = dados.consultar(QUERY_DESEMPENHO)

    col1, col2, col3 = st.columns(3)
    col1.metric("Professores", f"{len(materias)}")
    col2.metric("Aulas fora da matéria principal",
                f"{int(materias.aulas_fora_da_principal.sum())}",
                help=f"De um total de {int(materias.aulas.sum())} aulas na base.")
    col3.metric(
        "Declaram mais matérias do que lecionam",
        f"{int((materias.materias_declaradas > materias.materias_com_aula).sum())}",
        help="Professores cuja coluna materias_ensina lista mais matérias do que as "
             "que aparecem nas aulas dele.",
    )

    st.divider()
    st.markdown("**Matérias declaradas e matérias com aula**")
    st.caption(
        "todos os professores dão aula em exatamente uma matéria, independente de "
        "quantas declaram ensinar"
    )
    st.plotly_chart(grafico_declaradas_vs_lecionadas(materias),
                    use_container_width=True, config={"displayModeBar": False})

    st.divider()
    st.markdown("### Desempenho de cada professor, dentro da própria matéria")
    st.caption(
        "Dois indicadores do que passa pela mão do professor: a nota dos alunos nos "
        "simulados que ele criou e o comparecimento às aulas que ele deu."
    )

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Nota dos simulados criados pelo professor**")
        st.caption("o traço é o intervalo de 95%: quando dois se cruzam, a ordem não é confiável")
        st.plotly_chart(grafico_nota_por_professor(desempenho),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Comparecimento dos alunos às aulas do professor**")
        st.caption("eixo de 70 a 100, a faixa que a presença ocupa na base")
        st.plotly_chart(grafico_presenca_por_professor(desempenho),
                        use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver professores em tabela"):
        st.markdown("**Matérias declaradas e lecionadas**")
        st.dataframe(
            materias.rename(columns={
                "professor_id": "ID", "nome_professor": "Professor",
                "materia_principal": "Matéria principal",
                "materias_declaradas": "Matérias declaradas",
                "materias_com_aula": "Matérias com aula", "aulas": "Aulas",
                "aulas_fora_da_principal": "Aulas fora da principal",
            }),
            hide_index=True, use_container_width=True,
        )
        st.markdown("**Desempenho por professor**")
        st.dataframe(
            desempenho.rename(columns={
                "professor_id": "ID", "nome_professor": "Professor",
                "materia": "Matéria", "aulas": "Aulas", "presenca": "Presença (%)",
                "simulados": "Simulados", "resultados": "Resultados",
                "nota_mediana": "Nota mediana", "nota_media": "Nota média",
                "nota_desvio": "Desvio padrão", "limite_inferior": "Limite inferior",
                "limite_superior": "Limite superior",
            }),
            hide_index=True, use_container_width=True,
        )

    st.divider()
    st.markdown("#### O que os dados mostram")
    st.markdown(_texto(materias, desempenho))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        for nome in (QUERY_MATERIAS, QUERY_DESEMPENHO):
            st.caption(f"`src/dashboard/querys/{nome}.sql`")
            st.code(dados.ler_sql(nome), language="sql")
