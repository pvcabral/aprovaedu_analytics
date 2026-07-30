"""Paleta e especificações de marca dos gráficos.

A ordem dos slots categóricos é o mecanismo de segurança para daltonismo: série
nova pega o próximo slot, nunca uma cor gerada. As superfícies têm que casar com
as de `.streamlit/config.toml`.
"""

from __future__ import annotations

import plotly.graph_objects as go

# Superfícies (iguais às do config.toml)
SUPERFICIE = "#fcfcfb"
PLANO_PAGINA = "#f9f9f7"

# Paleta categórica, em ordem fixa. Uma série nova pega o próximo slot.
CATEGORICA = [
    "#2a78d6",  # 1 azul
    "#eb6834",  # 2 laranja
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 amarelo
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 verde
    "#4a3aa7",  # 7 violeta
    "#e34948",  # 8 vermelho
]

# Rampa sequencial de um só tom, para magnitude (claro -> escuro).
SEQUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#256abf", "#184f95"]

# A mesma rampa sequencial no formato que o Plotly espera, para mapa de calor.
ESCALA_SEQUENCIAL = [
    [posicao / (len(SEQUENCIAL) - 1), cor] for posicao, cor in enumerate(SEQUENCIAL)
]

# Rampa divergente, para valor com polaridade (acima e abaixo de um ponto
# neutro). Dois tons que leem como opostos, com cinza no meio: o meio precisa
# ler como "nada", e é por isso que não entra cor nele.
DIVERGENTE = [
    [0.0, "#2a78d6"],   # polo negativo, azul
    [0.5, "#f0efec"],   # neutro, cinza
    [1.0, "#e34948"],   # polo positivo, vermelho
]

# Cinza de contexto da forma "ênfase": uma série em cor, o resto recuado.
DE_ENFASE = "#c3c2b7"

# Tinta e cromo. Texto nunca veste a cor da série.
TINTA_PRIMARIA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_MUTED = "#898781"
GRADE = "#e1e0d9"
LINHA_BASE = "#c3c2b7"

# Status, reservado para estado (nunca para "série 4").
STATUS = {"bom": "#0ca30c", "atencao": "#fab219", "grave": "#ec835a", "critico": "#d03b3b"}

FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

# Especificações de marca
ESPESSURA_LINHA = 2
TAMANHO_MARCADOR = 8
LARGURA_ANEL = 2       # anel na cor da superfície, para marcador sobre linha
GAP_SUPERFICIE = 2     # separa fills que se tocam (segmentos de pilha, barras vizinhas)
RAIO_PONTA_BARRA = 4
OPACIDADE_AREA = 0.10


def aplicar_layout(
    fig: go.Figure,
    *,
    altura: int = 380,
    titulo_y: str | None = None,
    titulo_x: str | None = None,
    mostrar_grade_x: bool = False,
    legenda: bool = False,
    margem_esquerda: int | None = None,
) -> go.Figure:
    """Aplica o cromo padrão à figura: grade fina, eixos recuados e fontes.

    Args:
        fig: figura com os traces já montados.
        altura: altura em px.
        titulo_y: rótulo do eixo y.
        titulo_x: rótulo do eixo x.
        mostrar_grade_x: liga a grade vertical.
        legenda: liga a legenda. Obrigatória com duas ou mais séries.
        margem_esquerda: margem em px. Em gráfico horizontal precisa caber o nome
            de categoria mais longo, senão o texto é cortado.

    Returns:
        A mesma figura, com o layout aplicado.
    """
    if margem_esquerda is None:
        margem_esquerda = 64 if titulo_y else 48
    margem = dict(
        l=margem_esquerda,
        r=20,
        t=48 if legenda else 28,
        b=44 if titulo_x else 32,
    )

    fig.update_layout(
        height=altura,
        margin=margem,
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        font=dict(family=FONTE, size=13, color=TINTA_SECUNDARIA),
        hoverlabel=dict(
            font=dict(family=FONTE, size=13),
            bgcolor=SUPERFICIE,
            bordercolor=LINHA_BASE,
            font_color=TINTA_PRIMARIA,
        ),
        showlegend=legenda,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            x=0,
            title=None,
            # Ordem igual à de declaração das séries.
            traceorder="normal",
            font=dict(color=TINTA_SECUNDARIA),
        ),
        barcornerradius=RAIO_PONTA_BARRA,
    )
    # Grade e eixos sempre sólidos: tracejado lê como projeção ou limite.
    fig.update_yaxes(
        title=dict(text=titulo_y, font=dict(color=TINTA_MUTED, size=12)),
        showgrid=True,
        gridcolor=GRADE,
        gridwidth=1,
        zeroline=False,
        showline=False,
        ticks="",
        tickfont=dict(color=TINTA_MUTED, size=12),
    )
    fig.update_xaxes(
        title=dict(text=titulo_x, font=dict(color=TINTA_MUTED, size=12)),
        showgrid=mostrar_grade_x,
        gridcolor=GRADE,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor=LINHA_BASE,
        linewidth=1,
        ticks="",
        tickfont=dict(color=TINTA_MUTED, size=12),
    )
    return fig


def anotar_valor(
    fig: go.Figure,
    x,
    y,
    texto: str,
    *,
    deslocamento_y: int = -18,
    cor: str = TINTA_PRIMARIA,
) -> None:
    """Põe um rótulo direto num ponto, em tinta de texto.

    Args:
        fig: figura a anotar.
        x: posição no eixo x.
        y: posição no eixo y.
        texto: texto do rótulo.
        deslocamento_y: deslocamento vertical em px.
        cor: cor do texto.
    """
    fig.add_annotation(
        x=x,
        y=y,
        text=texto,
        showarrow=False,
        yshift=deslocamento_y,
        font=dict(family=FONTE, size=13, color=cor),
    )
