"""Camada de apresentação: dashboard Streamlit.

Divisão de responsabilidade dentro do pacote:

- `querys/`: um arquivo `.sql` por consulta, em SQL puro e sem parâmetro. É
  onde as métricas são definidas, e cada arquivo roda direto num cliente SQL.
- `dados.py`: lê e executa esses arquivos, com cache. Sem regra de negócio.
- `tema.py`: paleta e especificações de marca dos gráficos.
- `perguntas/`: uma página por pergunta do desafio.
"""
