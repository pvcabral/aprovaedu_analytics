"""Pergunta 3: desempenho por matéria e por curso, por nota e por aprovação."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, tema

QUERY_MATERIA_ANO = "p3_notas_por_materia_e_ano"
QUERY_MATERIA_SITUACAO = "p3_notas_por_materia_e_situacao"
QUERY_CURSO_ANO = "p3_aprovacoes_por_curso_e_ano"
QUERY_CURSO_NOTA = "p3_notas_vestibular_por_curso"
QUERY_VESTIBULAR_ANO = "p3_notas_vestibular_por_ano"
QUERY_SIM_VEST = "p3_simulado_vs_vestibular"
QUERY_SIM_VEST_ANO = "p3_diferenca_simulado_vestibular_por_ano"
QUERY_RELACAO = "p3_relacao_materia_e_curso"

APROVADO, NAO_APROVADO = "Aprovado", "Não aprovado"
MATERIA_SUBJETIVA = "redacao"


def _mapa_de_calor(
    matriz: pd.DataFrame,
    *,
    rotulo_valor: str,
    divergente: bool = False,
    limite: float | None = None,
    faixa: tuple[float, float] | None = None,
    casas: int = 1,
    altura: int = 420,
    margem_esquerda: int = 100,
) -> go.Figure:
    """Mapa de calor de categoria por ano, com o valor escrito na célula.

    Args:
        matriz: linhas são categorias, colunas são anos.
        rotulo_valor: nome do valor, na barra de escala e no tooltip.
        divergente: usa a rampa divergente centrada em zero.
        limite: extremo da escala divergente.
        faixa: (mínimo, máximo) da rampa sequencial.
        casas: casas decimais do rótulo na célula.
        altura: altura em px.
        margem_esquerda: espaço para o nome das categorias.
    

    Returns:
        A figura montada.
    """
    escala = tema.DIVERGENTE if divergente else tema.ESCALA_SEQUENCIAL
    fig = go.Figure(
        go.Heatmap(
            z=matriz.values,
            x=[str(coluna) for coluna in matriz.columns],
            y=list(matriz.index),
            colorscale=escala,
            zmid=0 if divergente else None,
            zmin=(-limite if (divergente and limite) else faixa[0] if faixa else None),
            zmax=(limite if (divergente and limite) else faixa[1] if faixa else None),
            xgap=tema.GAP_SUPERFICIE,
            ygap=tema.GAP_SUPERFICIE,
            text=matriz.round(casas).values,
            texttemplate="%{text}",
            textfont=dict(family=tema.FONTE, size=11),
            hovertemplate=(
                f"<b>%{{y}} · %{{x}}</b><br>{rotulo_valor}: %{{z}}<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text=rotulo_valor, font=dict(size=11, color=tema.TINTA_MUTED)),
                thickness=10,
                tickfont=dict(size=11, color=tema.TINTA_MUTED),
                outlinewidth=0,
            ),
        )
    )
    tema.aplicar_layout(fig, altura=altura, margem_esquerda=margem_esquerda)
    fig.update_xaxes(showgrid=False, side="top")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig


# ------------------------------------------------------- 1. nota por matéria
def grafico_mediana_por_materia_e_ano(materia_ano: pd.DataFrame) -> go.Figure:
    """Mediana da nota de simulado por matéria e ano, na escala fixa de 50 a 80.

    Returns:
        A figura montada.
    """
    matriz = materia_ano.pivot(index="nome_materia", columns="ano", values="mediana")
    matriz = matriz.loc[matriz.mean(axis=1).sort_values(ascending=False).index]
    return _mapa_de_calor(matriz, rotulo_valor="mediana", faixa=(50, 80),
                          altura=440, margem_esquerda=95)


def grafico_desvio_por_materia_e_ano(materia_ano: pd.DataFrame) -> go.Figure:
    """Desvio padrão da nota por matéria e ano, na escala fixa de 0 a 20.

    Returns:
        A figura montada.
    """
    matriz = materia_ano.pivot(index="nome_materia", columns="ano", values="desvio")
    ordem = materia_ano.pivot(index="nome_materia", columns="ano", values="mediana")
    matriz = matriz.loc[ordem.mean(axis=1).sort_values(ascending=False).index]
    return _mapa_de_calor(matriz, rotulo_valor="desvio", faixa=(0, 20),
                          altura=440, margem_esquerda=95)


# --------------------------------------------- 2. nota contra aprovação
def grafico_diferenca_aprovados(materia_situacao: pd.DataFrame) -> go.Figure:
    """Mediana dos aprovados menos a dos não aprovados, por matéria e ano.

    Positivo é matéria em que os aprovados foram melhores. Escala travada em 10
    pontos, uma diferença grande na régua de 0 a 100.

    Returns:
        A figura montada.
    """
    largo = materia_situacao.pivot_table(
        index=["nome_materia", "ano"], columns="situacao", values="mediana"
    )
    diferenca = (largo[APROVADO] - largo[NAO_APROVADO]).unstack()
    diferenca = diferenca.loc[diferenca.mean(axis=1).sort_values(ascending=False).index]
    return _mapa_de_calor(
        diferenca, rotulo_valor="diferença", divergente=True, limite=10.0,
        altura=440, margem_esquerda=95,
    )


# ----------------------------------------------------------- 3. cursos
def grafico_aprovados_por_curso_e_ano(curso_ano: pd.DataFrame) -> go.Figure:
    """Aprovados por curso e ano, em contagem.

    Returns:
        A figura montada.
    """
    matriz = curso_ano.pivot(index="curso_aprovado", columns="ano", values="aprovados")
    matriz = matriz.fillna(0)
    matriz = matriz.loc[matriz.sum(axis=1).sort_values(ascending=False).index]
    return _mapa_de_calor(matriz, rotulo_valor="aprovados", casas=0,
                          altura=480, margem_esquerda=170)


def grafico_nota_vestibular_por_ano(vestibular_ano: pd.DataFrame) -> go.Figure:
    """Mediana da nota de vestibular por ano, com a faixa do percentil 10 ao 90.

    Returns:
        A figura montada.
    """
    base = vestibular_ano.sort_values("ano")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=base.ano.tolist() + base.ano.tolist()[::-1],
            y=base.percentil_90.tolist() + base.percentil_10.tolist()[::-1],
            fill="toself",
            fillcolor="rgba(42, 120, 214, 0.10)",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=base.ano, y=base.mediana, mode="lines+markers",
            line=dict(color=tema.CATEGORICA[0], width=tema.ESPESSURA_LINHA),
            marker=dict(color=tema.CATEGORICA[0], size=tema.TAMANHO_MARCADOR,
                        line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL)),
            customdata=base[["aprovados", "desvio", "percentil_10", "percentil_90"]],
            hovertemplate=(
                "<b>%{x}</b><br>mediana: %{y:.1f}<br>desvio: %{customdata[1]:.1f}<br>"
                "faixa de 10% a 90%: %{customdata[2]:.0f} a %{customdata[3]:.0f}<br>"
                "%{customdata[0]} aprovados<extra></extra>"
            ),
            showlegend=False,
        )
    )
    tema.aplicar_layout(fig, altura=340, margem_esquerda=56)
    fig.update_yaxes(range=[450, 1000], dtick=100)
    fig.update_xaxes(tickmode="array", tickvals=base.ano.tolist())
    return fig


def grafico_nota_por_curso(curso_nota: pd.DataFrame) -> go.Figure:
    """Mediana da nota de vestibular por curso, com a faixa do percentil 10 ao 90.

    Returns:
        A figura montada.
    """
    ordenado = curso_nota.sort_values("mediana")
    fig = go.Figure()
    for _, linha in ordenado.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[linha.percentil_10, linha.percentil_90],
                y=[linha.curso_aprovado, linha.curso_aprovado],
                mode="lines", line=dict(color=tema.LINHA_BASE, width=6),
                hoverinfo="skip", showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=ordenado.mediana, y=ordenado.curso_aprovado, mode="markers",
            marker=dict(color=tema.CATEGORICA[0], size=tema.TAMANHO_MARCADOR + 2,
                        line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL)),
            customdata=ordenado[["aprovados", "desvio", "percentil_10", "percentil_90"]],
            hovertemplate=(
                "<b>%{y}</b><br>mediana: %{x:.1f}<br>desvio: %{customdata[1]:.1f}<br>"
                "faixa de 10% a 90%: %{customdata[2]:.0f} a %{customdata[3]:.0f}<br>"
                "%{customdata[0]} aprovados<extra></extra>"
            ),
            showlegend=False,
        )
    )
    tema.aplicar_layout(fig, altura=480, titulo_x="nota final de vestibular",
                        margem_esquerda=170)
    # Faixa fixa com folga: sem ela o eixo termina no maior percentil e a barra mais
    # longa encosta na borda.
    fig.update_xaxes(showgrid=True, gridcolor=tema.GRADE, range=[550, 950])
    fig.update_yaxes(showgrid=False, type="category")
    return fig


# --------------------------------------- 4. simulado contra vestibular
def grafico_simulado_vs_vestibular(pares: pd.DataFrame) -> go.Figure:
    """Nota de simulado contra nota de vestibular, com a linha de igualdade.

    Ponto acima da diagonal é aluno que foi melhor no vestibular.

    Returns:
        A figura montada.
    """
    limites = [40, 100]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=limites, y=limites, mode="lines",
            line=dict(color=tema.TINTA_MUTED, width=1),
            hoverinfo="skip", showlegend=False,
        )
    )
    fig.add_annotation(
        x=94, y=94, text="notas iguais", showarrow=False, textangle=-45,
        yshift=14, font=dict(family=tema.FONTE, size=11, color=tema.TINTA_MUTED),
    )
    fig.add_trace(
        go.Scatter(
            x=pares.nota_simulado, y=pares.vestibular_em_100, mode="markers",
            marker=dict(color=tema.CATEGORICA[0], size=7, opacity=0.55),
            customdata=pares[["ano", "diferenca", "nota_vestibular"]],
            hovertemplate=(
                "simulado: %{x:.1f}<br>vestibular: %{y:.1f} "
                "(%{customdata[2]:.1f} de 1000)<br>diferença: %{customdata[1]:+.1f}"
                "<br>ano: %{customdata[0]}<extra></extra>"
            ),
            showlegend=False,
        )
    )
    tema.aplicar_layout(fig, altura=420, titulo_x="nota média de simulado do aluno (0 a 100)",
                        margem_esquerda=64)
    fig.update_xaxes(range=limites, showgrid=True, gridcolor=tema.GRADE, dtick=10)
    fig.update_yaxes(range=limites, dtick=10,
                     title=dict(text="nota de vestibular na mesma régua (0 a 100)",
                                font=dict(color=tema.TINTA_MUTED, size=12)))
    return fig


def grafico_diferenca_por_ano(pares: pd.DataFrame) -> go.Figure:
    """Distribuição da diferença entre vestibular e simulado, uma caixa por ano.

    Returns:
        A figura montada.
    """
    fig = go.Figure()
    for ano in sorted(pares.ano.unique()):
        fig.add_trace(
            go.Box(
                name=str(ano), y=pares[pares.ano == ano].diferenca,
                marker=dict(color=tema.CATEGORICA[0], size=6, opacity=0.5),
                line=dict(color=tema.CATEGORICA[0], width=tema.ESPESSURA_LINHA),
                fillcolor="rgba(42, 120, 214, 0.10)",
                boxpoints="outliers",
                hovertemplate="%{y:.1f}<extra></extra>", showlegend=False,
            )
        )
    fig.add_hline(
        y=0, line=dict(color=tema.TINTA_MUTED, width=1),
        annotation_text="notas iguais", annotation_position="bottom right",
        annotation_font=dict(family=tema.FONTE, size=11, color=tema.TINTA_MUTED),
    )
    tema.aplicar_layout(fig, altura=420, margem_esquerda=64)
    fig.update_yaxes(title=dict(text="vestibular menos simulado",
                                font=dict(color=tema.TINTA_MUTED, size=12)))
    return fig


# -------------------------------------------- 5. relação matéria e curso
def grafico_relacao_area_curso(relacao: pd.DataFrame) -> go.Figure:
    """Escore z médio dos aprovados de cada curso, por área.

    Escala travada em um desvio padrão inteiro, que seria um efeito grande.

    Returns:
        A figura montada.
    """
    matriz = relacao.pivot(index="curso_aprovado", columns="area", values="z_medio")
    matriz = matriz.loc[matriz.mean(axis=1).sort_values(ascending=False).index]
    return _mapa_de_calor(
        matriz, rotulo_valor="escore z", divergente=True, limite=1.0, casas=2,
        altura=520, margem_esquerda=170,
    )


# ------------------------------------------------------------------ textos
def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto_materias(materia_ano: pd.DataFrame) -> str:
    """Monta o texto sobre as notas por matéria.

    Returns:
        O texto em markdown.
    """
    objetivas = materia_ano[materia_ano.nome_materia != MATERIA_SUBJETIVA]
    por_materia = objetivas.groupby("nome_materia").agg(
        mediana=("mediana", "mean"), desvio=("desvio", "mean"), p10=("percentil_10", "mean")
    )
    variacao = objetivas.groupby("nome_materia").mediana.agg(lambda s: s.max() - s.min())
    subjetiva = materia_ano[materia_ano.nome_materia == MATERIA_SUBJETIVA]

    texto = f"""
**Nenhuma matéria se destaca, em nenhum ano.** Entre as {len(por_materia)} matérias
objetivas, a mediana da nota fica entre {_num(por_materia.mediana.min())} e
{_num(por_materia.mediana.max())} numa escala de 0 a 100. Olhando ano a ano, a
mediana de uma mesma matéria varia no máximo {_num(variacao.max())} pontos entre o
melhor e o pior ano, e nenhuma matéria fica acima das outras de forma consistente. Não
existe aqui a matéria em que os alunos vão mal e que justificaria reforço.

**O desvio conta a mesma coisa.** Ele fica em torno de {_num(por_materia.desvio.mean())}
pontos em todas as matérias objetivas, ou seja, os alunos se espalham igual em todas
elas. Não há matéria que concentre os alunos nem matéria que separe forte de fraco.
"""

    if len(subjetiva):
        med_sub = subjetiva.mediana.mean()
        desvio_sub = subjetiva.desvio.mean()
        p10_sub = subjetiva.percentil_10.mean()
        texto += f"""
**Redação é o único caso diferente, e não por serem melhores nela.** A mediana dela é
{_num(med_sub)} contra {_num(por_materia.mediana.mean())} das objetivas, mas o que
explica isso é o espalhamento, não o desempenho. O desvio de redação é
{_num(desvio_sub)} contra {_num(por_materia.desvio.mean())} das objetivas, quase a
metade, e os 10% piores em redação ficam acima de {_num(p10_sub)}, contra
{_num(por_materia.p10.mean())} nas objetivas. É o comportamento esperado de correção
de texto: é avaliação subjetiva, e banca de redação raramente dá nota muito baixa.
Quase ninguém vai mal, e é isso que empurra a mediana para cima.
"""
    return texto.strip()


def _texto_nota_e_aprovacao(materia_situacao: pd.DataFrame) -> str:
    """Monta o texto sobre o cruzamento entre nota e aprovação.

    Returns:
        O texto em markdown.
    """
    largo = materia_situacao.pivot_table(
        index=["nome_materia", "ano"], columns="situacao", values="mediana"
    )
    diferenca = largo[APROVADO] - largo[NAO_APROVADO]
    favoravel = int((diferenca > 0).sum())
    total = len(diferenca)
    por_materia = diferenca.groupby("nome_materia").mean()
    consistentes = int(((diferenca > 0).groupby("nome_materia").sum() == 5).sum())

    return f"""
**Nota em matéria nenhuma separa quem passa de quem não passa.** Comparando a mediana
dos aprovados com a dos não aprovados em cada matéria e ano, os aprovados vão melhor
em {favoravel} das {total} combinações, quando o simples acaso daria cerca de {total / 2:.0f}.
A diferença média é de {_num(diferenca.mean())} ponto, praticamente
zero, e varia de {_num(diferenca.min())} a {_num(diferenca.max())} sem padrão.

**E nenhuma matéria é consistente.** {"Nenhuma das matérias tem" if consistentes == 0
else f"Apenas {consistentes} matéria tem"} os aprovados à frente nos cinco anos, que é
o que se esperaria de uma matéria que de fato pesasse na aprovação. No mapa acima, uma
matéria assim apareceria como uma linha vermelha inteira, e não existe nenhuma. A
matéria com a maior diferença média é {por_materia.idxmax()}, com
{_num(por_materia.max())} ponto, o que não sustenta decisão nenhuma.
"""


def _texto_cursos(curso_nota: pd.DataFrame, curso_ano: pd.DataFrame,
                  vestibular_ano: pd.DataFrame) -> str:
    """Monta o texto sobre desempenho por curso.

    Returns:
        O texto em markdown.
    """
    mais = curso_ano.groupby("curso_aprovado").aprovados.sum().sort_values(ascending=False)
    topo, base_ = curso_nota.iloc[0], curso_nota.iloc[-1]
    faixa_media = (curso_nota.percentil_90 - curso_nota.percentil_10).mean()
    diferenca_medianas = topo.mediana - base_.mediana

    return f"""
**Em volume, os cursos se distribuem de forma equilibrada.** O curso com mais
aprovados no período é {mais.index[0]}, com {int(mais.iloc[0])} de
{int(mais.sum())} aprovações, e o último da lista tem {int(mais.iloc[-1])}. Ano a ano
são poucas unidades por curso, então o número de um curso num ano isolado não diz
muita coisa; o padrão só aparece somando o período.

**Em nota, o ranking entre cursos não se sustenta.** A mediana vai de
{_num(base_.mediana)} ({base_.curso_aprovado}) a {_num(topo.mediana)}
({topo.curso_aprovado}), uma diferença de {_num(diferenca_medianas)} pontos. Só que a
faixa que cobre 80% dos aprovados de cada curso tem em média {_num(faixa_media)} pontos
de largura, várias vezes maior que a distância entre o primeiro e o último. As faixas
se sobrepõem quase inteiramente, e é por isso que trocar posições dessa lista não
significa nada.

**E a nota do curso não mede o cursinho.** Ela reflete a concorrência do curso, isto é,
quanto foi preciso tirar para entrar. Curso com mediana alta é curso disputado, não
curso em que o cursinho prepara melhor. Por ano, a mediana geral das notas de aprovação
fica entre {_num(vestibular_ano.mediana.min())} e {_num(vestibular_ano.mediana.max())},
também sem tendência.
"""


def _texto_simulado_vestibular(pares: pd.DataFrame, por_ano: pd.DataFrame) -> str:
    """Monta o texto sobre a calibragem entre simulado e vestibular.

    Returns:
        O texto em markdown.
    """
    melhores = (pares.diferenca > 0).mean() * 100
    piores = int((pares.diferenca < 0).sum())
    correlacao = pares.nota_simulado.corr(pares.vestibular_em_100)

    # Em quantos anos a metade central dos alunos fica inteira acima do zero, ou
    # seja, a caixa do gráfico não encosta na linha de igualdade.
    primeiro_quartil = pares.groupby("ano").diferenca.quantile(0.25)
    anos_acima = int((primeiro_quartil > 0).sum())
    anos_total = len(primeiro_quartil)
    ano_que_encosta = ", ".join(
        str(int(ano)) for ano in primeiro_quartil[primeiro_quartil <= 0].index
    )

    return f"""
**Para quem passou, o vestibular foi menos severo que os simulados do cursinho.** A
mediana da diferença é de {_num(pares.diferenca.median())} pontos na régua de 0 a 100,
a favor do vestibular, e {_num(melhores)}% dos {len(pares)} alunos tiraram no
vestibular mais do que a própria média de simulado. O padrão se repete nos cinco
anos, com mediana entre {_num(por_ano.diferenca_mediana.min())} e
{_num(por_ano.diferenca_mediana.max())} pontos. Não é efeito de poucos casos: em
{anos_acima} dos {anos_total} anos a metade central dos alunos fica inteira acima da
linha de igualdade{f", e só em {ano_que_encosta} a caixa encosta no zero"
if ano_que_encosta else ""}.

**Mas cuidado com a leitura, porque só os aprovados entram na conta.** Nota de
vestibular existe na base apenas para quem passou. E passar exige nota de vestibular
alta, então esse grupo já é, por construção, o dos que foram bem na prova. Parte da
diferença de {_num(pares.diferenca.median())} pontos é isso, e não calibragem do
simulado. Com esta base não dá para separar as duas coisas: faltaria a nota de quem
prestou e não passou.

**O que dá para afirmar com segurança.** Que o simulado não está superestimando o
aluno, o que seria o risco real: se estivesse, os aprovados apareceriam abaixo da
diagonal, e apenas {piores} dos {len(pares)} aparecem. E que a nota de simulado não
serve para prever nota de vestibular: a correlação entre as duas é de
{_num(correlacao, 3)}, praticamente zero, e a nuvem não tem inclinação. O simulado
funciona como treino e diagnóstico de conteúdo, não como estimativa de nota final.
"""


def _texto_relacao(relacao: pd.DataFrame) -> str:
    """Monta o texto sobre a relação entre matéria e curso.

    Returns:
        O texto em markdown.
    """
    limite = 2 * relacao.erro_padrao.median()
    acima = relacao[relacao.z_medio.abs() > 2 * relacao.erro_padrao]
    extremo = relacao.loc[relacao.z_medio.abs().idxmax()]
    esperado = 0.05 * len(relacao)
    quantas = (
        "**nenhuma** passa" if len(acima) == 0
        else f"**{len(acima)}** passa" if len(acima) == 1
        else f"apenas **{len(acima)}** passam"
    )

    return f"""
**Não há relação entre a matéria forte do aluno e o curso em que ele passou.** Se
existisse, os aprovados de medicina viriam acima da média em Natureza, os de engenharia
em Exatas, os de direito em Humanas. O mapa não mostra nada disso: de {len(relacao)}
combinações de curso e área, {quantas} de dois erros padrão, quando o próprio acaso
produziria cerca de {esperado:.0f}. O valor mais extremo da tabela é
{_num(extremo.z_medio, 2)}, em {extremo.curso_aprovado} e {extremo.area}, e nem ele
escapa da margem de erro.

**Por que a comparação foi feita por área e não matéria a matéria.** São
{int(relacao.groupby("area").aprovados.sum().max())} aprovados com simulado no período.
Cruzar 11 matérias com 14 cursos daria células de 2 alunos, onde qualquer número é
sorteio. Com as
5 áreas do ENEM cada célula tem algumas dezenas, e ainda assim a margem de cada uma
fica em torno de {_num(limite, 2)}. Valores até esse tamanho aparecem por acaso, e é
por isso que a escala de cor foi travada num efeito grande de verdade: célula pálida
significa efeito pequeno, que é o caso de todas.
"""


# ------------------------------------------------------------- renderização
def renderizar() -> None:
    """Renderiza a página da pergunta 3."""
    st.subheader("3. Quais cursos ou matérias apresentam melhor desempenho?")
    st.caption(
        "Desempenho medido por dois indicadores, nota e aprovação, sempre recortado "
        "por ano. As comparações usam mediana e desvio padrão: a mediana descreve o "
        "aluno típico sem ser deslocada por notas extremas, e o desvio é o que mostra "
        "desempenho fora da curva."
    )

    materia_ano = dados.consultar(QUERY_MATERIA_ANO)
    materia_situacao = dados.consultar(QUERY_MATERIA_SITUACAO)
    curso_ano = dados.consultar(QUERY_CURSO_ANO)
    curso_nota = dados.consultar(QUERY_CURSO_NOTA)
    vestibular_ano = dados.consultar(QUERY_VESTIBULAR_ANO)
    pares = dados.consultar(QUERY_SIM_VEST)
    sim_vest_ano = dados.consultar(QUERY_SIM_VEST_ANO)
    relacao = dados.consultar(QUERY_RELACAO)
    objetivas = materia_ano[materia_ano.nome_materia != MATERIA_SUBJETIVA]

    # ------------------------------------------------------- 1
    st.divider()
    st.markdown("### 1. Nota por matéria, ano a ano")
    st.caption(
        "Nota de simulado na escala de 0 a 100. Redação é corrigida de 0 a 1000 e "
        "entra reescalada, mas como é correção de texto ela não é comparável com as "
        "matérias objetivas."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Diferença entre a melhor e a pior matéria",
        f"{objetivas.groupby('nome_materia').mediana.mean().max() - objetivas.groupby('nome_materia').mediana.mean().min():.1f} pontos".replace(".", ","),
        help="Diferença entre as medianas, considerando só as matérias objetivas.",
    )
    col2.metric(
        "Desvio nas matérias objetivas",
        f"{objetivas.desvio.mean():.1f} pontos".replace(".", ","),
        help="Desvio padrão médio das notas. Mede o quanto os alunos se espalham.",
    )
    col3.metric(
        "Desvio em redação",
        f"{materia_ano.loc[materia_ano.nome_materia == MATERIA_SUBJETIVA, 'desvio'].mean():.1f} pontos".replace(".", ","),
        help="Quase a metade do desvio das objetivas: em redação praticamente "
             "ninguém tira nota muito baixa.",
    )

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Mediana da nota**")
        st.caption("onde está o aluno típico de cada matéria em cada ano")
        st.plotly_chart(grafico_mediana_por_materia_e_ano(materia_ano),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Desvio padrão da nota**")
        st.caption("o quanto os alunos se espalham em torno dessa mediana")
        st.plotly_chart(grafico_desvio_por_materia_e_ano(materia_ano),
                        use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver matéria e ano em tabela"):
        st.dataframe(
            materia_ano.rename(columns={
                "nome_materia": "Matéria", "ano": "Ano", "resultados": "Resultados",
                "alunos": "Alunos", "mediana": "Mediana", "media": "Média",
                "desvio": "Desvio padrão", "percentil_10": "Percentil 10",
                "percentil_90": "Percentil 90",
            }),
            hide_index=True, use_container_width=True,
        )

    st.markdown(_texto_materias(materia_ano))

    # ------------------------------------------------------- 2
    st.divider()
    st.markdown("### 2. Nota e aprovação, por matéria e ano")
    st.caption(
        "Mediana de quem passou no vestibular menos mediana de quem não passou, em "
        "cada matéria e ano. Vermelho é matéria em que os aprovados foram melhores, "
        "azul o contrário. Uma matéria que pesasse na aprovação apareceria como uma "
        "linha vermelha inteira."
    )

    st.plotly_chart(grafico_diferenca_aprovados(materia_situacao),
                    use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver nota por matéria, ano e situação em tabela"):
        st.dataframe(
            materia_situacao.rename(columns={
                "nome_materia": "Matéria", "ano": "Ano", "situacao": "Situação",
                "alunos": "Alunos", "mediana": "Mediana", "desvio": "Desvio padrão",
            }),
            hide_index=True, use_container_width=True,
        )

    st.markdown(_texto_nota_e_aprovacao(materia_situacao))

    # ------------------------------------------------------- 3
    st.divider()
    st.markdown("### 3. Aprovações e nota por curso, ano a ano")

    esquerda, direita = st.columns([3, 2])
    with esquerda:
        st.markdown("**Aprovados por curso e ano**")
        st.caption("contagem, o indicador de curso que não depende de estimativa")
        st.plotly_chart(grafico_aprovados_por_curso_e_ano(curso_ano),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Nota de aprovação por ano**")
        st.caption("mediana e a faixa que cobre 80% dos aprovados, todos os cursos")
        st.plotly_chart(grafico_nota_vestibular_por_ano(vestibular_ano),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("**Nota de vestibular por curso**")
    st.caption(
        "os cinco anos somados, porque por curso e ano sobram poucas unidades de "
        "aprovado e mediana de meia dúzia de valores não descreve nada. A barra vai "
        "do percentil 10 ao 90 e o ponto é a mediana"
    )
    st.plotly_chart(grafico_nota_por_curso(curso_nota), use_container_width=True,
                    config={"displayModeBar": False})

    with st.expander("Ver cursos em tabela"):
        st.markdown("**Nota por curso, somando os anos**")
        st.dataframe(
            curso_nota.rename(columns={
                "curso_aprovado": "Curso", "aprovados": "Aprovados",
                "mediana": "Mediana", "media": "Média", "desvio": "Desvio padrão",
                "percentil_10": "Percentil 10", "percentil_90": "Percentil 90",
            }),
            hide_index=True, use_container_width=True,
        )
        st.markdown("**Aprovações por curso e ano**")
        st.dataframe(
            curso_ano.rename(columns={
                "curso_aprovado": "Curso", "ano": "Ano", "aprovados": "Aprovados",
                "mediana": "Mediana", "desvio": "Desvio padrão",
            }),
            hide_index=True, use_container_width=True,
        )
        st.markdown("**Nota de aprovação por ano**")
        st.dataframe(
            vestibular_ano.rename(columns={
                "ano": "Ano", "aprovados": "Aprovados", "mediana": "Mediana",
                "media": "Média", "desvio": "Desvio padrão",
                "percentil_10": "Percentil 10", "percentil_90": "Percentil 90",
            }),
            hide_index=True, use_container_width=True,
        )

    st.markdown(_texto_cursos(curso_nota, curso_ano, vestibular_ano))

    # ------------------------------------------------------- 4
    st.divider()
    st.markdown("### 4. Simulado contra vestibular: qual prova foi mais severa?")
    st.caption(
        "As duas notas na mesma régua de 0 a 100: o simulado já vem nessa escala e a "
        "nota de vestibular, que vai até 1000, é dividida por 10. Só entram alunos "
        "aprovados, porque nota de vestibular só existe para quem passou."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alunos comparados", f"{len(pares)}",
                help="Aprovados que também têm simulado concluído no mesmo ano.")
    col2.metric(
        "Diferença mediana",
        f"{pares.diferenca.median():+.1f} pontos".replace(".", ","),
        help="Nota de vestibular menos nota de simulado, na régua de 0 a 100. "
             "Positivo significa que o aluno foi melhor no vestibular.",
    )
    col3.metric(
        "Desvio da diferença",
        f"{pares.diferenca.std():.1f} pontos".replace(".", ","),
        help="O quanto essa diferença varia de aluno para aluno.",
    )
    col4.metric(
        "Foram melhor no vestibular",
        f"{(pares.diferenca > 0).mean() * 100:.1f}%".replace(".", ","),
        help="Proporção dos aprovados com nota de vestibular acima da própria "
             "média de simulado.",
    )

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Cada aluno nas duas provas**")
        st.caption("ponto acima da diagonal é aluno que foi melhor no vestibular")
        st.plotly_chart(grafico_simulado_vs_vestibular(pares),
                        use_container_width=True, config={"displayModeBar": False})
    with direita:
        st.markdown("**Distribuição da diferença, ano a ano**")
        st.caption("a caixa cobre a metade central dos alunos e a linha é a mediana")
        st.plotly_chart(grafico_diferenca_por_ano(pares),
                        use_container_width=True, config={"displayModeBar": False})

    with st.expander("Ver a diferença por ano em tabela"):
        st.dataframe(
            sim_vest_ano.rename(columns={
                "ano": "Ano", "alunos": "Alunos",
                "simulado_mediana": "Simulado (mediana)",
                "vestibular_mediana": "Vestibular (mediana)",
                "diferenca_mediana": "Diferença (mediana)",
                "diferenca_desvio": "Diferença (desvio)",
                "pct_melhor_no_vestibular": "Melhor no vestibular (%)",
            }),
            hide_index=True, use_container_width=True,
        )

    st.markdown(_texto_simulado_vestibular(pares, sim_vest_ano))

    # ------------------------------------------------------- 5
    st.divider()
    st.markdown("### 5. Quem foi melhor em quais matérias passou em quais cursos?")
    st.caption(
        "As matérias são agrupadas nas áreas do ENEM: Exatas é matemática; Natureza é "
        "química, física e biologia; Humanas é história, geografia, filosofia e "
        "sociologia; Linguagens é português e inglês; Redação fica à parte. A nota é "
        "padronizada dentro de cada área e ano, então 0 é o aluno médio da área e "
        "positivo é acima dela."
    )

    st.plotly_chart(grafico_relacao_area_curso(relacao), use_container_width=True,
                    config={"displayModeBar": False})

    with st.expander("Ver escore por curso e área em tabela"):
        st.dataframe(
            relacao.rename(columns={
                "curso_aprovado": "Curso", "area": "Área", "aprovados": "Aprovados",
                "z_medio": "Escore médio", "erro_padrao": "Erro padrão",
            }),
            hide_index=True, use_container_width=True,
        )

    st.markdown(_texto_relacao(relacao))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        for nome in (QUERY_MATERIA_ANO, QUERY_MATERIA_SITUACAO, QUERY_CURSO_ANO,
                     QUERY_CURSO_NOTA, QUERY_VESTIBULAR_ANO, QUERY_SIM_VEST,
                     QUERY_SIM_VEST_ANO, QUERY_RELACAO):
            st.caption(f"`src/dashboard/querys/{nome}.sql`")
            st.code(dados.ler_sql(nome), language="sql")
