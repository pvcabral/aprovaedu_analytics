"""Formas de gráfico reaproveitadas pelas páginas, uma por trabalho de leitura.

A escala de cor e o eixo são sempre ancorados numa faixa passada por quem chama,
nunca no intervalo observado, para variação pequena não virar contraste visual.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.dashboard import tema


def pontos_com_intervalo(
    base: pd.DataFrame,
    *,
    coluna_categoria: str,
    coluna_valor: str,
    coluna_inferior: str,
    coluna_superior: str,
    titulo_x: str,
    faixa_x: tuple[float, float] | None = None,
    altura: int = 440,
    margem_esquerda: int = 100,
    hover_extra: list[str] | None = None,
    linha_referencia: float | None = None,
    rotulo_referencia: str | None = None,
    ordenar: bool = True,
) -> go.Figure:
    """Ranking de categorias com o intervalo de confiança desenhado.

    Args:
        base: uma linha por categoria.
        coluna_categoria: coluna com o nome da categoria.
        coluna_valor: coluna com a estimativa central.
        coluna_inferior: limite inferior do intervalo.
        coluna_superior: limite superior do intervalo.
        titulo_x: rótulo do eixo horizontal.
        faixa_x: limites do eixo.
        altura: altura em px.
        margem_esquerda: espaço para o nome das categorias.
        hover_extra: colunas extras no tooltip.
        linha_referencia: valor onde desenhar uma linha vertical de referência.
        rotulo_referencia: texto ao lado dessa linha.
        ordenar: ordena por valor. Desligue quando a ordem recebida já significa algo.

    Returns:
        A figura montada.
    """
    ordenado = base.sort_values(coluna_valor) if ordenar else base.iloc[::-1]
    colunas_hover = hover_extra or []
    fig = go.Figure()
    if linha_referencia is not None:
        fig.add_vline(
            x=linha_referencia,
            line=dict(color=tema.TINTA_MUTED, width=1),
            annotation_text=rotulo_referencia,
            annotation_position="top",
            annotation_font=dict(family=tema.FONTE, size=11, color=tema.TINTA_MUTED),
        )
    fig.add_trace(
        go.Scatter(
            x=ordenado[coluna_valor],
            y=ordenado[coluna_categoria],
            mode="markers",
            marker=dict(
                color=tema.CATEGORICA[0],
                size=tema.TAMANHO_MARCADOR + 2,
                line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL),
            ),
            error_x=dict(
                type="data",
                symmetric=False,
                array=ordenado[coluna_superior] - ordenado[coluna_valor],
                arrayminus=ordenado[coluna_valor] - ordenado[coluna_inferior],
                color=tema.LINHA_BASE,
                thickness=tema.ESPESSURA_LINHA,
                width=0,
            ),
            customdata=ordenado[[coluna_inferior, coluna_superior] + colunas_hover],
            hovertemplate=(
                "<b>%{y}</b><br>valor: %{x:.1f}<br>"
                "intervalo de 95%: %{customdata[0]:.1f} a %{customdata[1]:.1f}"
                + "".join(
                    f"<br>{coluna}: %{{customdata[{indice + 2}]}}"
                    for indice, coluna in enumerate(colunas_hover)
                )
                + "<extra></extra>"
            ),
        )
    )
    tema.aplicar_layout(fig, altura=altura, titulo_x=titulo_x,
                        margem_esquerda=margem_esquerda)
    fig.update_xaxes(showgrid=True, gridcolor=tema.GRADE)
    fig.update_yaxes(showgrid=False, type="category")
    if faixa_x:
        fig.update_xaxes(range=list(faixa_x))
    return fig


def faixa_com_mediana(
    base: pd.DataFrame,
    *,
    coluna_categoria: str,
    coluna_mediana: str,
    coluna_inferior: str,
    coluna_superior: str,
    titulo_x: str,
    faixa_x: tuple[float, float] | None = None,
    altura: int = 440,
    margem_esquerda: int = 100,
    hover_extra: list[str] | None = None,
) -> go.Figure:
    """Barra do percentil baixo ao alto, com a mediana marcada por um ponto.

    Args:
        base: uma linha por categoria.
        coluna_categoria: coluna com o nome da categoria.
        coluna_mediana: coluna da mediana.
        coluna_inferior: coluna do percentil baixo.
        coluna_superior: coluna do percentil alto.
        titulo_x: rótulo do eixo horizontal.
        faixa_x: limites do eixo.
        altura: altura em px.
        margem_esquerda: espaço para o nome das categorias.
        hover_extra: colunas extras no tooltip.

    Returns:
        A figura montada.
    """
    ordenado = base.sort_values(coluna_mediana)
    colunas_hover = hover_extra or []
    fig = go.Figure()
    for _, linha in ordenado.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[linha[coluna_inferior], linha[coluna_superior]],
                y=[linha[coluna_categoria], linha[coluna_categoria]],
                mode="lines",
                line=dict(color=tema.LINHA_BASE, width=6),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=ordenado[coluna_mediana],
            y=ordenado[coluna_categoria],
            mode="markers",
            marker=dict(
                color=tema.CATEGORICA[0],
                size=tema.TAMANHO_MARCADOR + 2,
                line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL),
            ),
            customdata=ordenado[[coluna_inferior, coluna_superior] + colunas_hover],
            hovertemplate=(
                "<b>%{y}</b><br>mediana: %{x:.1f}<br>"
                "faixa: %{customdata[0]:.1f} a %{customdata[1]:.1f}"
                + "".join(
                    f"<br>{coluna}: %{{customdata[{indice + 2}]}}"
                    for indice, coluna in enumerate(colunas_hover)
                )
                + "<extra></extra>"
            ),
            showlegend=False,
        )
    )
    tema.aplicar_layout(fig, altura=altura, titulo_x=titulo_x,
                        margem_esquerda=margem_esquerda)
    fig.update_xaxes(showgrid=True, gridcolor=tema.GRADE)
    fig.update_yaxes(showgrid=False, type="category")
    if faixa_x:
        fig.update_xaxes(range=list(faixa_x))
    return fig


def mapa_de_calor(
    matriz: pd.DataFrame,
    *,
    rotulo_valor: str,
    faixa: tuple[float, float] | None = None,
    divergente: bool = False,
    limite: float | None = None,
    casas: int = 1,
    altura: int = 440,
    margem_esquerda: int = 100,
) -> go.Figure:
    """Mapa de calor de uma matriz de categoria por ano, com o valor na célula.

    Args:
        matriz: linhas são categorias, colunas são anos.
        rotulo_valor: nome do valor, na barra de escala e no tooltip.
        faixa: (mínimo, máximo) da rampa sequencial.
        divergente: usa a rampa divergente centrada em zero.
        limite: extremo da rampa divergente.
        casas: casas decimais do rótulo na célula.
        altura: altura em px.
        margem_esquerda: espaço para o nome das categorias.

    Returns:
        A figura montada.
    """
    fig = go.Figure(
        go.Heatmap(
            z=matriz.values,
            x=[str(coluna) for coluna in matriz.columns],
            y=list(matriz.index),
            colorscale=tema.DIVERGENTE if divergente else tema.ESCALA_SEQUENCIAL,
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


def haltere(
    largo: pd.DataFrame,
    *,
    grupos: tuple[str, str],
    titulo_x: str,
    faixa_x: tuple[float, float] | None = None,
    altura: int = 320,
    margem_esquerda: int = 100,
    sufixo: str = "",
) -> go.Figure:
    """Duas marcas ligadas por um traço em cada categoria, uma por grupo.

    Args:
        largo: índice é a categoria, com uma coluna por grupo.
        grupos: nomes das duas colunas de grupo, na ordem da legenda.
        titulo_x: rótulo do eixo horizontal.
        faixa_x: limites do eixo.
        altura: altura em px.
        margem_esquerda: espaço para o nome das categorias.
        sufixo: sufixo dos valores no eixo e no tooltip, por exemplo "%".

    Returns:
        A figura montada. Categoria sem um dos grupos aparece com uma marca só.
    """
    primeiro, segundo = grupos
    categorias = [str(indice) for indice in largo.index]
    fig = go.Figure()

    # Conector primeiro, para as marcas ficarem por cima. Acesso por rótulo porque
    # `itertuples` renomeia coluna com espaço ou acento.
    for categoria, (_, linha) in zip(categorias, largo.iterrows()):
        valores = [linha[primeiro], linha[segundo]]
        if any(pd.isna(valor) for valor in valores):
            continue
        fig.add_trace(
            go.Scatter(
                x=valores, y=[categoria, categoria], mode="lines",
                line=dict(color=tema.LINHA_BASE, width=tema.ESPESSURA_LINHA),
                hoverinfo="skip", showlegend=False,
            )
        )

    for indice, grupo in enumerate((primeiro, segundo)):
        fig.add_trace(
            go.Scatter(
                name=grupo, x=largo[grupo], y=categorias, mode="markers",
                marker=dict(
                    color=tema.CATEGORICA[indice], size=13,
                    line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL),
                ),
                hovertemplate=(
                    f"<b>%{{y}} · {grupo}</b><br>%{{x:.1f}}{sufixo}<extra></extra>"
                ),
            )
        )

    tema.aplicar_layout(fig, altura=altura, titulo_x=titulo_x, legenda=True,
                        margem_esquerda=margem_esquerda)
    fig.update_xaxes(showgrid=True, gridcolor=tema.GRADE, ticksuffix=sufixo)
    # Ordem fixada: sem isso o Plotly ordena por primeira aparição e a categoria
    # sem conector cai para o fim.
    fig.update_yaxes(showgrid=False, type="category",
                     categoryorder="array", categoryarray=categorias)
    if faixa_x:
        fig.update_xaxes(range=list(faixa_x))
    return fig
