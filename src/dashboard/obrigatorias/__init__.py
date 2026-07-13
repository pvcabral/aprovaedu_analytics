"""Aba de análises obrigatórias do dashboard.

Cada pergunta do desafio vira uma sub-aba, renderizada por um módulo
próprio em `src/dashboard/obrigatorias/`.
"""

import streamlit as st

from src.dashboard.obrigatorias import (
    taxa_aprovacao,
    presenca_aprovados,
    desempenho,
    recomendacoes,
)


def renderizar() -> None:
    """Renderiza as 4 perguntas obrigatórias do desafio, uma por aba."""
    aba_1, aba_2, aba_3, aba_4 = st.tabs(
        [
            "1. Taxa de aprovação",
            "2. Presença x aprovação",
            "3. Desempenho",
            "4. Recomendações",
        ]
    )

    with aba_1:
        taxa_aprovacao.renderizar()

    with aba_2:
        presenca_aprovados.renderizar()

    with aba_3:
        desempenho.renderizar()

    with aba_4:
        recomendacoes.renderizar()