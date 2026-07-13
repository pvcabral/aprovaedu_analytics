# Relatório final: Desafio LogAp

Este relatório reúne as respostas às perguntas obrigatórias do desafio, com os
principais achados e recomendações. Todas as análises foram geradas a partir dos
dados já processados (ver o [README.md](README.md) para rodar o pipeline).

Uma observação vale para tudo o que vem a seguir: a base analisada é uma
**amostra**. A maioria das tabelas vem cortada em cerca de 500 linhas, e cada
aba foi amostrada de forma independente. Por isso vários cruzamentos ficam com
poucas dezenas de alunos, e alguns recortes cobrem só parte da realidade. As
conclusões são, então, indícios que apontam direções, e cada análise deixa o
tamanho da base à vista. A confirmação definitiva depende da base completa.

## Taxa de aprovação

### Como a taxa foi definida

A taxa foi medida sobre os **alunos matriculados em cada ano**, e não pela
simples contagem das linhas da tabela de aprovações. A ideia é responder a uma
pergunta concreta: dos alunos que fizeram o cursinho em um determinado ano,
quantos prestaram o vestibular daquele mesmo ano e passaram. Assim, cada aluno
entra na conta do ano em que de fato esteve matriculado, e a aprovação só conta
quando acontece no vestibular do mesmo ano.

Essa escolha organiza os alunos nos seus devidos anos e evita uma leitura
enganosa: contar as aprovações soltas somaria passagens sem saber se aquele
aluno estava matriculado naquele período, e misturaria anos diferentes. Medindo
sobre a coorte de matriculados, a taxa passa a significar "efetividade do preparo
daquele ano", que é o que interessa para a coordenação.

O denominador (matriculados) vem de uma tabela amostrada, mas o numerador é
conferido contra a tabela de aprovações, que é a base completa do desafio. Ou
seja, quando um matriculado não aparece como aprovado, isso é real, e não um
dado que faltou por amostragem.

### Resultado

| Ano | Matriculados | Aprovados | Taxa de aprovação | Evolução vs. ano anterior |
|---|---:|---:|---:|---:|
| 2021 | 9 | 3 | 33,3% | - |
| 2022 | 15 | 4 | 26,7% | -19,8% |
| 2023 | 15 | 7 | 46,7% | +74,9% |
| 2024 | 12 | 6 | 50,0% | +7,1% |
| 2025 | 6 | 4 | 66,7% | +33,4% |

A taxa cresce de forma consistente no período. Depois de uma queda de 2021 para
2022 (-19,8%), a evolução é sempre positiva: um salto forte de 2022 para 2023
(+74,9%), um avanço menor de 2023 para 2024 (+7,1%) e outro salto de 2024 para
2025 (+33,4%). No total do intervalo, a taxa praticamente dobra, saindo de um
terço dos matriculados para dois terços.

### Leitura

É um excelente resultado, e sugere que o preparo vem ficando mais efetivo ano a
ano. Ainda assim, ele não é totalmente confiável por causa da limitação dos
dados: a amostra de matrículas cobre poucos alunos por ano (entre 6 e 15), então
a taxa deve ser lida como uma tendência encorajadora, não como o número fechado
do curso. Com a base completa de matrículas, dá para confirmar se o crescimento
se sustenta.

### Recorte por bolsa

Junto da taxa, vale olhar quantos dos aprovados passaram com bolsa (integral ou
parcial) e quantos sem bolsa, por ano:

| Ano | Com bolsa | Sem bolsa | Não informado |
|---|---:|---:|---:|
| 2021 | 20 | 6 | 5 |
| 2022 | 10 | 6 | 14 |
| 2023 | 28 | 14 | 15 |
| 2024 | 33 | 7 | 8 |
| 2025 | 30 | 12 | 11 |

O número de aprovados com bolsa cresce ao longo dos anos (com uma queda pontual
em 2022) e se mantém acima dos sem bolsa. A bolsa é um dado que não dá para
deixar de lado, mas aqui a leitura precisa ser cuidadosa: sem conhecer a política
de bolsas do cursinho, não dá para afirmar se os bolsistas representam retorno
financeiro direto. É possível, por exemplo, que a bolsa funcione como marketing,
atraindo mais matrículas e aprovações, o que seria um retorno indireto. O que o
dado mostra é que a bolsa tem peso relevante no perfil das aprovações e merece
ser acompanhada de perto, cruzando com a política real do curso.

## Presença x aprovação

### Como foi medido

O objetivo foi cruzar presença com aprovação para ter uma ideia de se as aulas
estão tendo impacto direto no retorno para os estudantes. Para isso, cada aluno
com presença registrada foi classificado como aprovado ou não aprovado, e
comparamos a taxa de presença dos dois grupos.

Duas decisões deixam a leitura mais correta. Primeiro, a presença foi amarrada
ao ano da aula (via `aula_id`), e só é comparada com a aprovação do mesmo ano.
Isso evita misturar a presença de um ano com a aprovação de outro, mantendo
sempre a lógica de métrica por ano, mesmo que aqui só exista dado de 2021.
Segundo, consideramos apenas os alunos que de fato têm presença registrada, e a
situação de aprovação é conferida contra a base completa de aprovações, então
"não aprovado" é real.

### Resultado

| Ano | Situação | Alunos | Taxa de presença |
|---|---|---:|---:|
| 2021 | Aprovado | 16 | 79,0% |
| 2021 | Não aprovado | 31 | 76,0% |

### Leitura

Os alunos aprovados frequentaram um pouco mais as aulas do que os não aprovados,
mas a diferença é muito pequena: cerca de 3 pontos percentuais, menos de 4% em
termos relativos. É pouco para afirmar que existe uma relação forte entre
presença e aprovação, ainda mais tendo apenas 2021 e poucas dezenas de alunos.
A leitura fica fraca justamente porque não temos toda a presença dos estudantes.

Um ponto chama mais atenção do que o gap entre os grupos: as duas taxas ficam
logo acima de 70%. Esse patamar costuma ser o mínimo que muitos cursos exigem
para considerar o aluno apto, então ver a frequência geral rondando esse limite
diz mais do que a pequena diferença entre aprovados e não aprovados.

### Recomendação

Presença não parece ser uma métrica que a coordenação precise vigiar como preditor
de aprovação ou reprovação, pelo menos com os dados atuais. O que vale investigar
é o motivo de a frequência estar tão perto dos 70%, porque isso pode indicar
descaso ou desengajamento dos estudantes, independentemente de passarem ou não.
Como todo o resto, não dá para concluir muito com uma amostra de um único ano, e
uma leitura firme depende da presença de todos os anos.

## Desempenho

A pergunta tem duas leituras possíveis, "matéria" e "curso", que vivem em lugares
diferentes da base e respondem a coisas diferentes. Além delas, incluí alguns
recortes complementares que ajudam a entender o desempenho.

### Desempenho por matéria

| Matéria | Nota média | Nota mediana | Resultados |
|---|---:|---:|---:|
| Matemática | 61,0 | 59,9 | 337 |
| Física | 60,6 | 59,5 | 86 |

Esta foi a leitura mais limitada da análise. A intenção era comparar o
desempenho entre as disciplinas do cursinho a partir das notas de simulado, mas a
amostra de resultados só cobre matemática e física, e as duas ficam praticamente
empatadas (média em torno de 60). Sem as outras nove matérias, não dá para dizer
quais disciplinas rendem melhor, e ainda estamos olhando só para exatas. É, das
análises, a que mais depende de mais dados para virar uma resposta de verdade.

### Desempenho por curso

Medido pela nota final de vestibular por curso da universidade em que os alunos
foram aprovados. Diferente da matéria, aqui o dado vem da base completa de
aprovações, então é sólido.

| Curso | Nota média de vestibular | Aprovados |
|---|---:|---:|
| Ciência da computação | 754,4 | 16 |
| Administração | 753,6 | 24 |
| Design | 741,5 | 25 |
| ... | ... | ... |
| Arquitetura | 707,3 | 27 |
| Direito | 706,1 | 26 |
| Engenharia civil | 701,5 | 26 |

As maiores notas ficam em ciência da computação e administração, e as menores em
engenharia civil e direito, num intervalo relativamente estreito (cerca de 700 a
754). Vale lembrar que isso mede o resultado no vestibular por curso pretendido, e
não a facilidade ou o domínio de uma disciplina no preparo. É a resposta mais
confiável para a pergunta, mas responde ao lado "curso", não ao lado "matéria".

### Nota de simulado x nota do vestibular

Entre os alunos aprovados que também têm simulado, quase 90% tiraram nota maior no
vestibular do que nos simulados, com uma diferença média em torno de 12 pontos na
mesma escala 0 a 100. Isso é positivo: mostra que o simulado é mais exigente que a
prova real, então o aluno chega bem preparado e rende ainda mais na hora que
conta. Não é caso de mexer numa dificuldade que vem funcionando.

### Nota de simulado x aprovação

Olhando a taxa de aprovação por faixa de nota de simulado, ela não cresce com a
nota, e a faixa mais alta chega a ter a menor taxa:

| Faixa de nota de simulado | Alunos | Taxa de aprovação |
|---|---:|---:|
| Abaixo de 50 | 19 | 42,1% |
| 50 a 60 | 44 | 29,5% |
| 60 a 70 | 54 | 44,4% |
| 70 ou mais | 21 | 23,8% |

Que a taxa não cresça com a nota é esperado. A aprovação depende de muitos fatores
que não estão nesta base, como a frequência, as condições da prova e até a
integridade das respostas nos simulados. São muitas possibilidades e outliers em
jogo. A conclusão prática é que a nota de simulado serve bem como diagnóstico de
estudo, mas não deve ser lida isoladamente como previsão de quem passa.

### Desempenho por modalidade de ensino (análise extra)

| Modalidade | Taxa de aprovação |
|---|---:|
| Híbrido | 45,5% |
| Presencial | 44,1% |
| Online | 39,1% |

O online de fato rende um pouco menos que o presencial e o híbrido, mas o quadro
está bem equilibrado. Não é um caso de reduzir a modalidade, e sim de, no máximo,
revisar as tutorias e o suporte que estão sendo oferecidos no online. Como as
outras, é uma leitura de base pequena e serve mais como sinal do que como
veredito.

## Recomendações para a coordenação

A leitura geral é positiva. O modelo de preparo vem funcionando, com destaque
para as turmas híbridas, os simulados estão num nível de exigência adequado, e a
taxa de aprovação dos matriculados evoluiu bem ao longo dos anos. A ressalva que
vale para tudo é que a maior parte dessas leituras se apoia em amostras pequenas,
então o passo mais importante antes de qualquer decisão de peso é conseguir a
base completa.

O primeiro ponto é um mérito que não dá para deixar de fora: a evolução da taxa de
aprovação. Ela praticamente dobrou de 2021 a 2025, saindo de cerca de um terço dos
matriculados para dois terços, com crescimento consistente ano a ano. É um sinal
forte de que o preparo vem ficando mais efetivo, e a coordenação deve reconhecer e
sustentar o que está gerando esse resultado.

A partir daí, três frentes merecem atenção prática:

**Turmas online.** A modalidade online mostrou taxa de aprovação um pouco abaixo
da presencial e da híbrida. O quadro está equilibrado e não pede uma mudança
drástica, mas vale revisar as tutorias e o suporte oferecidos no online para
entender e reduzir essa diferença.

**Presença.** A frequência dos alunos ficou logo acima de 70%, o patamar que
costuma ser o mínimo aceitável. Mais do que a relação com aprovação, que se
mostrou fraca, o que merece investigação é o motivo dessa frequência baixa, que
pode indicar desengajamento dos estudantes.

**Bolsas.** A bolsa tem peso relevante no perfil das aprovações e cresceu ao longo
dos anos. Vale validar a política de bolsas junto ao retorno real que ela traz,
seja financeiro direto, seja indireto, como atração de novas matrículas.

Por fim, o que está funcionando deve ser mantido: a exigência dos simulados, que
prepara bem os alunos, e o modelo híbrido. E o que trava conclusões mais firmes é
a falta de dados. Para projetar tudo com segurança, o ideal é consolidar a base
completa, principalmente os resultados de simulado de todas as matérias (hoje só
matemática e física), a presença de todos os anos (hoje só 2021) e o cadastro
completo de estudantes. Com esses dados, praticamente todas as leituras deste
relatório podem sair de indício para conclusão.

## Próximos passos com a base completa

Com a base completa em mãos, o plano seria voltar à etapa exploratória e mapear o
que os dados realmente permitem, levantando novas possibilidades de métricas e
cruzamentos que hoje ficam inviáveis pelo tamanho da amostra. A partir de uma base
consistente, o passo seguinte seria partir para modelos de machine learning para
prever aprovação a partir do perfil do aluno, da frequência, das notas de simulado
e das demais variáveis.

Outra evolução que deixaria o relatório mais dinâmico seria conectar cada análise a
uma API de inteligência artificial, que geraria um parecer sobre aquele dado logo
abaixo do gráfico, comentando o que se vê e sugerindo leituras. Para não consultar
a IA a cada visualização e evitar custos desnecessários, esse parecer ficaria
armazenado em cache, sendo regerado apenas quando o dado por trás mudasse.

