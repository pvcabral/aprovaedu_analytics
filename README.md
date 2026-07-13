# Desafio LogAp: AprovaEdu Analytics

Pipeline que trata uma base fictícia de um curso pré-vestibular, carrega os dados
num banco Postgres modelado com PK e FK, e apresenta as análises num dashboard
Streamlit. Tudo sobe com um único comando via Docker.

As respostas às perguntas obrigatórias, os achados e as recomendações estão no
[RELATORIO.md](RELATORIO.md).

## Ferramentas utilizadas

- **Python 3.11** para o tratamento e a orquestração.
- **pandas** e **openpyxl** para ler e tratar a planilha Excel.
- **PostgreSQL 16** como banco analítico, com **SQLAlchemy** e **psycopg2**.
- **Streamlit** e **Plotly** para o dashboard.
- **Docker** e **Docker Compose** para subir tudo (banco, carga e dashboard).

## Como rodar

Pré-requisito: Docker e Docker Compose instalados.

1. Clone o repositório e entre na pasta:

   ```bash
   git clone <url-do-repositorio>
   cd desafio_logap
   ```

2. Crie o arquivo de configuração a partir do modelo:

   ```bash
   cp .env.example .env
   ```

   Ajuste a senha e, se quiser, as portas.

3. Suba o projeto:

   ```bash
   docker compose up --build
   ```

   Isso vai, na ordem:
   - subir o Postgres e esperar ele ficar saudável;
   - rodar o `main.py`, que cria o schema, trata a planilha, carrega as tabelas
     no banco e exporta os CSVs tratados em `data/tratados/`;
   - subir o dashboard Streamlit.

4. Acesse o dashboard em **http://localhost:8501**.

Para conferir os dados direto no banco:

```bash
docker exec -it desafio_logap_db psql -U logap -d desafio_logap
```

### Se algo der errado ao subir

- **Parece travado ou sem logs**: rode sem `-d` para ver o log em tempo real, ou
  use `docker compose logs -f app`.
- **Não abre no navegador (WSL)**: se `http://localhost:8501` não abrir, use o IP
  do WSL (`hostname -I`) na porta 8501.
- **Banco com dados de execução anterior**: `docker compose down -v` remove o
  volume do Postgres antes de subir de novo.
- **Suspeita de cache de build**: `docker compose build --no-cache`.

## Estrutura do projeto

```
.
├── app.py                          # ponto de entrada do dashboard Streamlit
├── main.py                         # ponto de entrada da carga (trata, carrega e exporta CSV)
├── docker-compose.yml              # sobe Postgres + carga + dashboard
├── Dockerfile
├── requirements.txt
├── .env.example                    # modelo de configuração (copie para .env)
├── data/
│   ├── base_pre_vestibular_dicionario_amostras.xlsx  # base de origem (amostra)
│   └── tratados/                   # CSVs tratados, gerados pelo main.py
├── src/
│   ├── banco.py                    # classe BancoDados (conexão e queries)
│   ├── schema.sql                  # DDL: tabelas, PKs e FKs
│   ├── tratamentos/
│   │   ├── tratamento_tabelas.py   # tratamento de cada tabela
│   │   └── tratamento_utils.py     # utilitários de limpeza reutilizados
│   └── dashboard/
│       ├── dados.py                # consultas que alimentam os gráficos
│       └── obrigatorias/           # uma sub-aba por pergunta obrigatória
│           ├── taxa_aprovacao.py
│           ├── presenca_aprovados.py
│           ├── desempenho.py
│           └── recomendacoes.py
└── RELATORIO.md                    # relatório final com as respostas e achados
```

## Dados tratados

Ao rodar o `main.py`, cada tabela final vai para `data/tratados/<tabela>.csv`, com
o conteúdo exatamente como ficou no banco: já com o tratamento, os filtros de FK e
os cadastros de estudante gerados na carga. É o artefato de base tratada, e fica
disponível mesmo sem subir o Postgres.

## Decisões técnicas relevantes

**Modelagem em Postgres com PK e FK.** A base foi modelada como um esquema
relacional (ver `src/schema.sql`). Ele tem uma dimensão de matérias (`dim_materia`)
gerada no tratamento e um relacionamento N:N `professor_materia`. Toda coluna que
referencia matéria usa o mesmo nome `materia_id`, para deixar explícito que é FK.

**A base é uma amostra, não a base completa.** A maioria das tabelas vem cortada
em cerca de 500 linhas, e cada aba foi amostrada de forma independente. Por isso
alguns cruzamentos têm poucas dezenas de registros, e alguns recortes cobrem só
parte da realidade. Os resultados de simulado, por exemplo, só existem para
matemática e física, e a presença em aula só cobre 2021. As análises tratam isso
de forma explícita.

**Estudantes stub para preservar dados linkáveis.** A amostra de estudantes é
incompleta, então aprovações, presenças e simulados de alunos fora dela seriam
descartados pela FK com `estudantes`. Para não perder esse dado, o `main.py` cria
cadastros mínimos (stub, com `nome_aluno = 'cadastro ausente'`) para todo
`aluno_id` que aparece nos fatos mas não no cadastro. Isso mantém a integridade
referencial e ainda permite medir quantos alunos faltam no cadastro para cada
métrica.

**Tratamento centralizado e reutilizável.** O `tratamento_utils.py` concentra a
limpeza que se repetia célula a célula: normalização de texto, conversão de datas
em formatos mistos, tratamento de nulos disfarçados de string, criação de
dimensões e mapeamento de categoria para id.

**Outliers de nota capados, não descartados.** As notas de simulado acima do
limite da escala (100) são capadas no próprio limite. Assim não se perde o
registro do aluno nem se deixa um valor extremo inflar a média.

**Alinhamento por ano nos cruzamentos.** Sempre que uma análise cruza dois fatos
com data (matrícula e aprovação, simulado e vestibular, presença e aprovação), o
casamento é feito pelo mesmo ano. Isso evita comparar um evento de um ano com
outro de um ano diferente.

## Decisões analíticas (resumo)

As perguntas obrigatórias foram respondidas sempre sobre os dados processados.
Cada análise deixa o N à vista e sinaliza quando o resultado é apenas indício por
causa do tamanho da amostra. O detalhamento das respostas, dos achados e das
recomendações está no [RELATORIO.md](RELATORIO.md).

## Demonstração

O dashboard sobe junto com o `docker compose up` e fica em **http://localhost:8501**,
com uma aba para cada pergunta obrigatória e uma aba de recomendações.
