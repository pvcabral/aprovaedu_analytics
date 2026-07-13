"""Ponto de entrada do dashboard Streamlit do projeto desafio_logap."""

import streamlit as st

from src.dashboard import obrigatorias

st.set_page_config(page_title="Desafio LogAp", layout="wide")

st.title("Desafio LogAp")

obrigatorias.renderizar()
