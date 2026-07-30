"""Uma página por análise.

Cada módulo expõe `renderizar()` e monta suas figuras em funções `grafico_*` que
recebem DataFrame e devolvem `go.Figure`, sem dependência de Streamlit, assim cada
gráfico pode ser conferido fora do app.

As páginas numeradas respondem as perguntas obrigatórias do desafio. As marcadas
como "Extra" são análises adicionais.
"""

from src.dashboard.perguntas import (
    extra_modalidade,
    extra_professores,
    extra_simulados,
    p1_taxa_aprovacao,
    p2_presenca_aprovacao,
    p3_desempenho,
    p4_recomendacoes,
)

# Rótulo exibido na navegação -> módulo que renderiza a página.
PAGINAS = {
    "1. Taxa de aprovação": p1_taxa_aprovacao,
    "2. Presença e aprovação": p2_presenca_aprovacao,
    "3. Desempenho por matéria e curso": p3_desempenho,
    "4. Recomendações": p4_recomendacoes,
    "Extra · Professores e matérias": extra_professores,
    "Extra · Modelo de ensino": extra_modalidade,
    "Extra · Aplicação dos simulados": extra_simulados,
}

__all__ = [
    "PAGINAS",
    "p1_taxa_aprovacao",
    "p2_presenca_aprovacao",
    "p3_desempenho",
    "p4_recomendacoes",
    "extra_professores",
    "extra_modalidade",
    "extra_simulados",
]
