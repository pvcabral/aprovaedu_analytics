"""Leitura e execução das consultas `.sql` do dashboard."""

from __future__ import annotations

import os

import pandas as pd
import psycopg2.errors
import streamlit as st
from sqlalchemy.exc import ProgrammingError

from src.banco import BancoDados

DIRETORIO_QUERYS = os.path.join(os.path.dirname(__file__), "querys")

# Erros de estrutura, traduzidos em `consultar` para uma mensagem acionável.
ERROS_DE_ESTRUTURA = (psycopg2.errors.UndefinedColumn, psycopg2.errors.UndefinedTable)


def caminho_query(nome: str) -> str:
    """Resolve o caminho do arquivo .sql.

    Args:
        nome: nome do arquivo, com ou sem `.sql`.

    Returns:
        Caminho do arquivo.

    Raises:
        FileNotFoundError: se não existir consulta com esse nome.
    """
    arquivo = nome if nome.endswith(".sql") else f"{nome}.sql"
    caminho = os.path.join(DIRETORIO_QUERYS, arquivo)
    if not os.path.exists(caminho):
        disponiveis = sorted(
            f[:-4] for f in os.listdir(DIRETORIO_QUERYS) if f.endswith(".sql")
        )
        raise FileNotFoundError(
            f"consulta '{nome}' não existe em {DIRETORIO_QUERYS}. "
            f"Disponíveis: {disponiveis}"
        )
    return caminho


def ler_sql(nome: str) -> str:
    """Lê o texto de uma consulta.

    Args:
        nome: nome do arquivo, com ou sem `.sql`.

    Returns:
        O SQL como texto.
    """
    with open(caminho_query(nome), encoding="utf-8") as arquivo:
        return arquivo.read()


@st.cache_data(ttl=600, show_spinner="Consultando o banco...")
def consultar(nome: str) -> pd.DataFrame:
    """Roda a consulta no Postgres, com o resultado em cache.

    Args:
        nome: nome do arquivo em `querys/`, com ou sem `.sql`.

    Returns:
        DataFrame com o resultado.

    Raises:
        RuntimeError: se a consulta pedir coluna ou tabela inexistente, o que
            costuma significar banco carregado antes da última mudança de schema.
    """
    sql = ler_sql(nome)
    banco = BancoDados()
    try:
        banco.conectar()
        return banco.consultar(sql)
    except ProgrammingError as erro:
        if isinstance(getattr(erro, "orig", None), ERROS_DE_ESTRUTURA):
            detalhe = str(erro.orig).splitlines()[0]
            raise RuntimeError(
                f"A consulta '{nome}' pede algo que não existe no banco: {detalhe} "
                "Isso costuma acontecer quando o banco foi carregado antes de uma "
                "mudança no schema. Rode a carga de novo para recriar as tabelas: "
                "'docker compose restart app', ou 'python main.py' se o Streamlit "
                "estiver rodando fora do Docker."
            ) from erro
        raise
    finally:
        banco.desconectar()
