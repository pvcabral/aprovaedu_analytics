"""Ponto de entrada do dashboard Streamlit.

Uma página por pergunta do desafio, escolhida na barra lateral. O app só
apresenta: as métricas são definidas nos arquivos `.sql` de
`src/dashboard/querys/`, e o tratamento e a carga dos dados ficam no `main.py`.
"""

import streamlit as st

from src.dashboard import tema
from src.dashboard.perguntas import PAGINAS

st.set_page_config(
    page_title="AprovaEdu Analytics",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    f"""
    <style>
      /* Bloco de conteúdo sobre o plano da página, com respiro. */
      .block-container {{ padding-top: 2.5rem; max-width: 1400px; }}
      /* Métricas como stat tiles: superfície de card e anel fino. */
      div[data-testid="stMetric"] {{
        background: {tema.SUPERFICIE};
        border: 1px solid rgba(11, 11, 11, 0.10);
        border-radius: 8px;
        padding: 14px 16px;
      }}
      div[data-testid="stMetricLabel"] p {{ color: {tema.TINTA_SECUNDARIA}; }}
      div[data-testid="stMetricValue"] {{ color: {tema.TINTA_PRIMARIA}; }}
      hr {{ border-color: {tema.GRADE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("AprovaEdu Analytics")
    st.caption(
        "Base fictícia de um curso pré-vestibular, 2021 a 2025. "
        "Uma página por pergunta do desafio."
    )
    escolha = st.radio("Análise", list(PAGINAS), label_visibility="collapsed")
    st.divider()
    st.caption(
        "As páginas numeradas respondem as perguntas obrigatórias do desafio. As "
        "marcadas como **Extra** são análises adicionais."
    )
    st.caption(
        "As consultas ficam em `src/dashboard/querys/`, em SQL puro, para rodar "
        "direto num cliente SQL."
    )

PAGINAS[escolha].renderizar()
