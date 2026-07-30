"""Gera as imagens usadas no RELATORIO.md a partir dos dados no banco.

Reaproveita as mesmas funções de gráfico do dashboard, então imagem e tela nunca
divergem. Requer o banco já carregado pelo `main.py` e o pacote `kaleido`:

    pip install -r requirements.txt kaleido==0.2.1
    python scripts/gerar_imagens_relatorio.py
"""

from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from src.banco import BancoDados  # noqa: E402
from src.dashboard import dados  # noqa: E402
from src.dashboard.perguntas import (  # noqa: E402
    p1_taxa_aprovacao as p1,
    p2_presenca_aprovacao as p2,
    p3_desempenho as p3,
    p4_recomendacoes as p4,
)

DESTINO = os.path.join(RAIZ, "docs", "imagens")


def main() -> None:
    """Consulta o banco, monta cada figura e grava o PNG em `docs/imagens/`."""
    banco = BancoDados()
    banco.conectar()
    try:
        consultar = lambda nome: banco.consultar(dados.ler_sql(nome))  # noqa: E731
        taxa_ano = consultar(p1.QUERY_PRINCIPAL)
        por_faixa = consultar(p2.QUERY_POR_FAIXA)
        materia_ano = consultar(p3.QUERY_MATERIA_ANO)
        materia_situacao = consultar(p3.QUERY_MATERIA_SITUACAO)
        curso_nota = consultar(p3.QUERY_CURSO_NOTA)
        pares = consultar(p3.QUERY_SIM_VEST)
        relacao = consultar(p3.QUERY_RELACAO)
        fatores = consultar(p4.QUERY_FATORES)
    finally:
        banco.desconectar()

    figuras = [
        ("fatores-testados", p4.grafico_fatores_testados(fatores), 1000, 340),
        ("taxa-por-ano", p1.grafico_taxa_por_ano(taxa_ano), 900, 360),
        ("aprovacao-por-faixa-de-presenca",
         p2.grafico_aprovacao_por_faixa(por_faixa), 900, 340),
        ("mediana-por-materia", p3.grafico_mediana_por_materia_e_ano(materia_ano), 760, 440),
        ("desvio-por-materia", p3.grafico_desvio_por_materia_e_ano(materia_ano), 760, 440),
        ("nota-e-aprovacao-por-materia",
         p3.grafico_diferenca_aprovados(materia_situacao), 1000, 440),
        ("nota-por-curso", p3.grafico_nota_por_curso(curso_nota), 1000, 480),
        ("simulado-vs-vestibular", p3.grafico_simulado_vs_vestibular(pares), 700, 480),
        ("relacao-area-e-curso", p3.grafico_relacao_area_curso(relacao), 1000, 520),
        ("crescimento-indexado", p4.grafico_crescimento(taxa_ano), 900, 340),
    ]

    os.makedirs(DESTINO, exist_ok=True)
    for nome, figura, largura, altura in figuras:
        caminho = os.path.join(DESTINO, f"{nome}.png")
        figura.write_image(caminho, width=largura, height=altura, scale=2)
        print(f"  -> {nome}.png")
    print(f"\n{len(figuras)} imagens geradas em {DESTINO}")


if __name__ == "__main__":
    main()
