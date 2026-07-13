"""Pergunta obrigatória 4: recomendações para a coordenação do cursinho.

Texto de parecer construído a partir das leituras das perguntas 1 a 3.
Começa pela limitação de dados (a base analisada é só amostra) e depois
apresenta recomendações práticas, sempre sinalizando o grau de confiança
de cada uma.
"""

import streamlit as st


def renderizar() -> None:
    """Renderiza o parecer e as recomendações para a coordenação."""
    st.subheader("Recomendações para a coordenação")

    st.warning(
        "Vale contextualizar antes de ler os números: esta análise foi feita em "
        "cima de uma **amostra** da base (a maioria das tabelas vem cortada em "
        "500 linhas, cada uma amostrada de forma independente). Por isso alguns "
        "cruzamentos ficam com poucas dezenas de alunos, e alguns recortes cobrem "
        "só parte da realidade, por exemplo os resultados de simulado só existem "
        "para **matemática e física**, e a presença em aula só cobre **2021**. "
        "Então trate as conclusões abaixo como **indícios que apontam direções**, "
        "não como números fechados. A recomendação mais importante de todas é "
        "consolidar a base completa (os CSVs integrais) antes de qualquer decisão "
        "definitiva, com ela dá pra confirmar ou descartar praticamente todas as "
        "leituras daqui com segurança."
    )

    st.markdown(
"""### Parecer sobre o que os dados atuais sugerem

Mesmo com a ressalva acima, o que temos já aponta direções úteis para a gestão
do cursinho.

**Manter e monitorar de perto o modelo de preparo atual, que vem entregando
resultado crescente.** A evidência está na taxa de aprovação dos matriculados:
entre os alunos que se matricularam, a fração aprovada no vestibular do mesmo
ano subiu de cerca de um terço nos primeiros anos para cerca de dois terços nos
mais recentes. É um sinal positivo e consistente, que precisa ser confirmado
com a base completa, já que hoje se apoia em poucas dezenas de alunos por ano.

**Sustentar a política de bolsas e passar a medir seu custo-benefício de forma
sistemática.** Isso porque o número de aprovados com bolsa (integral ou parcial)
cresceu ao longo dos anos e se manteve acima do número de aprovados sem bolsa.
O dado sugere que a bolsa está associada a boa parte das aprovações, mas só a
base completa permite dizer se ela de fato amplia o acesso e converte em
resultado, ou se apenas acompanha o crescimento geral.

**Não priorizar acompanhamento de frequência como alavanca de aprovação.** No
único ano com dados de presença (2021), aprovados e não aprovados frequentaram
as aulas de forma parecida — 84,6% contra 80,8% de comparecimento. Não existe um
grupo faltoso entre os não aprovados que justifique alertas de falta ou busca
ativa como prioridade. Vale reavaliar quando houver presença dos demais anos.

**Reforçar o suporte às turmas online antes de expandi-las.** O motivo é que a
taxa de aprovação da modalidade online ficou abaixo da presencial e da híbrida
(aproximadamente 39% na online contra 44% na presencial e 46% na híbrida). Vale
investigar a experiência do aluno online (tutoria, suporte, engajamento) e
confirmar o padrão com mais dados antes de qualquer decisão de escala.

**Manter o nível de exigência dos simulados, que parece bem ajustado, e não usar
a nota deles isoladamente como previsão de aprovação.** Dois sinais sustentam
isso. Primeiro, entre os aprovados, quase 90% tiraram nota maior no vestibular do
que nos simulados, com uma diferença média em torno de 12 pontos na mesma escala
0-100. Isso é positivo: mostra que o simulado é mais exigente que a prova real,
então o aluno chega bem preparado e rende ainda mais na hora que conta, e não faz
sentido mexer numa dificuldade que vem funcionando. Segundo, a nota de simulado
não se relacionou com passar no vestibular: a taxa de aprovação por faixa de nota
não cresce com a nota, e a faixa mais alta chega a ter a menor taxa. Ou seja, o
simulado serve bem como diagnóstico de estudo, mas a nota isolada não prevê quem
passa e não deve ser lida assim. Como todo o resto, precisa ser confirmado: hoje
só há simulado de matemática e física, de um único ano.

### O que priorizar na coleta de dados

Para transformar esses indícios em decisões seguras, o mais urgente é obter a
base completa de resultados de simulado cobrindo todas as matérias. Hoje só há
matemática e física, o que impede avaliar o desempenho por disciplina. Em
seguida, a presença de todos os anos, não só 2021, para medir a relação entre
frequência e aprovação de forma robusta. Por fim, o cadastro completo de
estudantes, que hoje vem incompleto e limita análises por perfil (cidade,
escola de origem, canal de captação).
"""
    )
