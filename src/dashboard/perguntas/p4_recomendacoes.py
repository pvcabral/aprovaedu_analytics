"""Pergunta 4: recomendações para a coordenação, sintetizando as análises."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import dados, graficos, tema

QUERY_FATORES = "p4_fatores_testados"
QUERY_TAXA_ANO = "p1_taxa_aprovacao_por_ano"
QUERY_SIM_VEST = "p3_simulado_vs_vestibular"
QUERY_PROFESSORES = "ex_professores_materias"


def grafico_fatores_testados(fatores: pd.DataFrame) -> go.Figure:
    """Efeito de cada fator na taxa de aprovação, com intervalo de 95%.

    Mantém a ordem da consulta: ordenar por efeito sugeriria ranking de importância.

    Returns:
        A figura montada.
    """
    fig = graficos.pontos_com_intervalo(
        fatores,
        coluna_categoria="fator",
        coluna_valor="diferenca_pp",
        coluna_inferior="limite_inferior",
        coluna_superior="limite_superior",
        titulo_x="diferença na taxa de aprovação, em pontos percentuais",
        faixa_x=(-25, 25),
        altura=340,
        margem_esquerda=210,
        hover_extra=["taxa_alto", "taxa_baixo", "n_alto", "n_baixo"],
        linha_referencia=0,
        rotulo_referencia="sem efeito",
        ordenar=False,
    )
    fig.update_xaxes(ticksuffix=" pp")
    return fig


def grafico_crescimento(taxa_ano: pd.DataFrame) -> go.Figure:
    """Matriculados e aprovados por ano, indexados em 100 no primeiro ano.

    O índice permite comparar as duas séries sem um segundo eixo.

    Returns:
        A figura montada.
    """
    base = taxa_ano.sort_values("ano")
    fig = go.Figure()
    for indice, (nome, coluna) in enumerate(
        (("Matriculados", "matriculados"), ("Aprovados", "aprovados"))
    ):
        indice_base = base[coluna].iloc[0]
        serie = 100 * base[coluna] / indice_base
        cor = tema.CATEGORICA[indice]
        fig.add_trace(
            go.Scatter(
                name=nome, x=base.ano, y=serie, mode="lines+markers",
                line=dict(color=cor, width=tema.ESPESSURA_LINHA),
                marker=dict(color=cor, size=tema.TAMANHO_MARCADOR,
                            line=dict(color=tema.SUPERFICIE, width=tema.LARGURA_ANEL)),
                customdata=base[[coluna]],
                hovertemplate=(
                    f"<b>{nome} · %{{x}}</b><br>índice: %{{y:.0f}}<br>"
                    "valor: %{customdata[0]}<extra></extra>"
                ),
            )
        )
    fig.add_hline(
        y=100, line=dict(color=tema.TINTA_MUTED, width=1),
        annotation_text=f"base {int(base.ano.iloc[0])}",
        annotation_position="bottom left",
        annotation_font=dict(family=tema.FONTE, size=11, color=tema.TINTA_MUTED),
    )
    tema.aplicar_layout(fig, altura=340, legenda=True, margem_esquerda=56)
    fig.update_yaxes(range=[80, 200], dtick=20)
    fig.update_xaxes(tickmode="array", tickvals=base.ano.tolist())
    return fig


def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto_fatores(fatores: pd.DataFrame) -> str:
    """Monta o texto sobre os fatores testados.

    Returns:
        O texto em markdown.
    """
    cruzam_zero = int(((fatores.limite_inferior < 0) & (fatores.limite_superior > 0)).sum())
    maior = fatores.loc[fatores.diferenca_pp.abs().idxmax()]

    return f"""
**Nenhum dos {len(fatores)} fatores testados distingue quem passa de quem não passa.**
Todos os {cruzam_zero} intervalos cruzam o zero, o que significa que a diferença medida
não se separa de nenhuma diferença. O maior efeito de toda a tabela é o de
{maior.fator.lower()}, com {_num(maior.diferenca_pp)} pontos percentuais, e mesmo ele vai
de {_num(maior.limite_inferior)} a {_num(maior.limite_superior)}.

**Vale notar qual é esse maior efeito: a diferença entre dois anos.** A oscilação natural
de um ano para o outro é maior do que qualquer fator que a coordenação controla. Isso é o
retrato de um cursinho cuja conversão não depende, de forma mensurável, de presença,
desempenho em simulado, nota de entrada ou formato de aula.
"""


def _texto_recomendacoes(fatores: pd.DataFrame, taxa_ano: pd.DataFrame,
                         pares: pd.DataFrame, professores: pd.DataFrame) -> str:
    """Monta as recomendações, cada uma com o número que a sustenta.

    Returns:
        O texto em markdown.
    """
    primeiro, ultimo = taxa_ano.iloc[0], taxa_ano.iloc[-1]
    cresc_matric = (ultimo.matriculados / primeiro.matriculados - 1) * 100
    cresc_aprov = (ultimo.aprovados / primeiro.aprovados - 1) * 100
    modelo = fatores[fatores.fator == "Modelo de ensino"].iloc[0]
    declaram_mais = int((professores.materias_declaradas > professores.materias_com_aula).sum())

    return f"""
**1. Parar de ler a nota do simulado como previsão de vestibular.** Entre os aprovados, a
nota de vestibular ficou {_num(pares.diferenca.median())} pontos acima da média de
simulado do próprio aluno, e a correlação entre as duas notas é de
{_num(pares.nota_simulado.corr(pares.vestibular_em_100), 3)}, ou seja, zero. Saber que um
aluno tira 55 no simulado não diz nada sobre a nota que ele fará na prova. O simulado
serve como diagnóstico de conteúdo, e é assim que deve ser apresentado ao aluno e à
família. Se a coordenação quiser um termômetro de aprovação, ele precisa ser construído e
validado, porque hoje não existe.

**2. Decidir modalidade por custo e alcance, não por eficácia.** Quem estudou só online
teve {_num(modelo.taxa_alto)}% de aprovação contra {_num(modelo.taxa_baixo)}% de quem
estudou em unidade física, uma diferença de {_num(modelo.diferenca_pp)} ponto com
intervalo de {_num(modelo.limite_inferior)} a {_num(modelo.limite_superior)}. A frequência
também é igual entre modalidades de aula, com 0,2 ponto de diferença. Como o formato não
muda o resultado, a escolha fica liberada para o critério que de fato varia: custo por
aluno, alcance geográfico e capacidade de sala. O mesmo raciocínio vale para dispositivo e
local de aplicação do simulado, onde a nota varia menos de um ponto: não há retorno em
padronizar equipamento.

**3. Para mais aprovados, crescer matrícula é o caminho comprovado; ganho de eficiência
não está à vista.** De {int(primeiro.ano)} a {int(ultimo.ano)} a matrícula cresceu
{_num(cresc_matric)}% e os aprovados {_num(cresc_aprov)}%, com a taxa parada em torno de
33%. Crescer funcionou e não diluiu a qualidade. O que a base não oferece é qualquer
alavanca de conversão: nenhum fator testado a move. Então uma meta de aprovados deve ser
planejada por volume de matrícula, e uma meta de taxa de aprovação precisa antes de um
diagnóstico que esta base não permite fazer.

**4. Resolver a habilitação dos professores, que hoje é ficção ou capacidade ociosa.**
{declaram_mais} dos {len(professores)} professores declaram ensinar mais matérias do que
lecionam: o cadastro lista duas ou três, e todos dão aula em exatamente uma. São duas
leituras possíveis e as duas pedem ação. Se a segunda habilitação é real, existe
flexibilidade de escala que não está sendo usada, o que importa em férias, licença e
abertura de turma. Se não é real, o cadastro está errado e vai embasar uma decisão ruim
algum dia.
"""


def _texto_medicao(pares: pd.DataFrame) -> str:
    """Monta o texto sobre o que passar a registrar.

    Returns:
        O texto em markdown.
    """
    return f"""
Boa parte do que a coordenação gostaria de saber não está respondida aqui por falta de
registro, e não por falta de análise. Em ordem de impacto:

**1. A nota de vestibular de quem não passou.** Hoje a base só tem nota de aprovado,
então a comparação entre simulado e vestibular usa {len(pares)} alunos que, por definição,
foram bem na prova. Sem a nota de quem prestou e não passou, não há como medir a eficácia
do preparo, nem calibrar o simulado, nem saber a que distância do corte os alunos ficaram.
É o registro que mais destravaria análise.

**2. Todas as aulas dadas.** As aulas registradas somam 2.645 horas contra 9.302
contratadas nas ofertas, 28,4% do total, com 8 a 14 aulas por oferta. Como consequência,
a frequência mede comparecimento às aulas registradas, e não frequência no curso. Métrica
de carga horária cumprida é inviável enquanto isso não mudar.

**3. Presença de quem falta muito.** A presença na base vai de 70,3% a 97,1%, e metade
dos alunos fica entre 81% e 87%. Não existe aluno de presença baixa. Ou o cursinho não tem
problema de evasão de aula, o que seria notável, ou esses alunos não estão sendo
registrados. Vale confirmar qual dos dois, porque a conclusão de que presença não afeta
aprovação vale para a faixa observada, e não para quem falta de verdade.

**4. Campos que chegam pela metade.** Tentativas do simulado não é informada em 16,9% dos
resultados; 253 aulas (10,5%) têm data anterior ao início da própria oferta; e as datas
chegam em quatro formatos diferentes, um deles com mês antes do dia. Nada disso invalida
as análises atuais, mas cada um cobra um tratamento que poderia não existir se a entrada
fosse padronizada.
"""


def _texto_guardrails(fatores: pd.DataFrame) -> str:
    """Monta o texto sobre o que não decidir com estes números.

    Returns:
        O texto em markdown.
    """
    return """
Este dashboard também serve para evitar decisão mal fundamentada. Quatro coisas que os
números **não** autorizam:

**Não ranquear matéria, curso ou professor com os números atuais.** As medianas existem e
podem ser ordenadas, mas as margens de erro se sobrepõem em todos os três casos. Entre as
matérias objetivas, a diferença entre primeira e última é de pouco mais de um ponto numa
escala de 0 a 100. Entre cursos, a faixa que cobre 80% dos aprovados de cada um tem 207
pontos de largura, contra 66 pontos de distância entre o primeiro e o último. Trocar
posições dessas listas não significa nada.

**Não criar reforço para "matéria fraca".** Ela não existe nesta base. Os três indicadores
por matéria, nota, conclusão de simulado e presença, ficam na mesma faixa estreita, e a
nota em matéria nenhuma separa aprovado de não aprovado em nenhum ano.

**Não tratar redação como a matéria em que os alunos vão melhor.** A nota dela é mais alta
porque é correção de texto: o desvio é 11,5 contra 18,0 das objetivas, e os 10% piores em
redação ficam acima de 58, contra 38 nas objetivas. Quase ninguém vai muito mal, e é isso
que empurra a mediana para cima.
"""


def renderizar() -> None:
    """Renderiza a página de recomendações."""
    st.subheader("4. Quais recomendações você faria para a coordenação do cursinho?")
    st.caption(
        "Síntese das análises anteriores. As recomendações estão organizadas pelo que "
        "os dados sustentam: o que fazer, o que passar a medir, e o que não decidir "
        "com estes números."
    )

    fatores = dados.consultar(QUERY_FATORES)
    taxa_ano = dados.consultar(QUERY_TAXA_ANO)
    pares = dados.consultar(QUERY_SIM_VEST)
    professores = dados.consultar(QUERY_PROFESSORES)

    primeiro, ultimo = taxa_ano.iloc[0], taxa_ano.iloc[-1]
    media = taxa_ano.aprovados.sum() / taxa_ano.matriculados.sum() * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fatores testados", f"{len(fatores)}",
                help="Presença, nota de simulado, nota diagnóstica, modelo de ensino e ano.")
    col2.metric(
        "Fatores com efeito comprovado",
        f"{int(((fatores.limite_inferior > 0) | (fatores.limite_superior < 0)).sum())}",
        help="Fatores cujo intervalo de 95% não cruza o zero.",
    )
    col3.metric("Taxa média do período", f"{media:.1f}%".replace(".", ","))
    col4.metric(
        "Crescimento de aprovados",
        f"+{(ultimo.aprovados / primeiro.aprovados - 1) * 100:.0f}%",
        help=f"De {int(primeiro.aprovados)} em {int(primeiro.ano)} para "
             f"{int(ultimo.aprovados)} em {int(ultimo.ano)}.",
    )

    st.divider()
    st.markdown("### O que move a taxa de aprovação")
    st.caption(
        "cada fator comparando seu grupo alto com seu grupo baixo, na mesma unidade: "
        "pontos percentuais de taxa de aprovação. Intervalo que cruza a linha do zero "
        "é fator sem efeito detectável"
    )
    st.plotly_chart(grafico_fatores_testados(fatores), use_container_width=True,
                    config={"displayModeBar": False})

    with st.expander("Ver os fatores testados em tabela"):
        st.dataframe(
            fatores.rename(columns={
                "fator": "Fator", "rotulo_alto": "Grupo alto",
                "rotulo_baixo": "Grupo baixo", "n_alto": "Alunos (alto)",
                "n_baixo": "Alunos (baixo)", "taxa_alto": "Taxa alto (%)",
                "taxa_baixo": "Taxa baixo (%)", "diferenca_pp": "Diferença (pp)",
                "erro_padrao": "Erro padrão", "limite_inferior": "Limite inferior",
                "limite_superior": "Limite superior",
            }),
            hide_index=True, use_container_width=True,
        )

    st.markdown(_texto_fatores(fatores))

    st.divider()
    st.markdown("### O que funcionou, e vale continuar")
    st.caption(
        "matriculados e aprovados em índice, com o primeiro ano valendo 100: a "
        "inclinação de cada linha é o crescimento, e as duas sobem quase juntas"
    )
    st.plotly_chart(grafico_crescimento(taxa_ano), use_container_width=True,
                    config={"displayModeBar": False})

    st.divider()
    st.markdown("### Recomendações")
    st.markdown(_texto_recomendacoes(fatores, taxa_ano, pares, professores))

    st.divider()
    st.markdown("### O que passar a registrar")
    st.markdown(_texto_medicao(pares))

    st.divider()
    st.markdown("### O que não decidir com estes números")
    st.markdown(_texto_guardrails(fatores))

    st.divider()
    with st.expander("Ver o SQL desta análise"):
        st.caption(
            "As demais consultas citadas estão nas páginas de origem de cada análise."
        )
        st.caption(f"`src/dashboard/querys/{QUERY_FATORES}.sql`")
        st.code(dados.ler_sql(QUERY_FATORES), language="sql")
