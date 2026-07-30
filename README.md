# Desafio LogAp: AprovaEdu Analytics

Pipeline que extrai a base de um zip, trata os dados, carrega num Postgres modelado
com PK e FK, e apresenta as análises num dashboard Streamlit. Tudo sobe com um único
comando via Docker.

As respostas às perguntas obrigatórias, os achados e as recomendações estão no
[RELATORIO.md](RELATORIO.md).

## Ferramentas utilizadas

- **Python 3.11** para a extração, o tratamento e a orquestração.
- **pandas** para ler e tratar os CSVs da base.
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

2. Coloque o **zip da base** dentro de `data/`. O nome não importa, só precisa ser o
   único `.zip` na pasta. Ele é descompactado a cada execução, então nada precisa ser
   preparado à mão.

3. Crie o arquivo de configuração a partir do modelo:

   ```bash
   cp .env.example .env
   ```

   Ajuste a senha e, se quiser, as portas.

4. Suba o projeto:

   ```bash
   docker compose up --build
   ```

   Isso vai, na ordem:
   - subir o Postgres e esperar ele ficar saudável;
   - rodar o `main.py`, que extrai o zip, trata os dados, cria o schema, carrega as
     tabelas no banco e exporta os CSVs tratados em `data/tratados/`;
   - subir o dashboard Streamlit.

5. Acesse o dashboard em **http://localhost:8501**.

Para conferir os dados direto no banco:

```bash
docker exec -it desafio_logap_db psql -U logap -d desafio_logap
```

### Se algo der errado ao subir

- **`Nenhum arquivo .zip encontrado em data/`**: o zip da base não está na pasta.
  Coloque ali e suba de novo.
- **`Mais de um .zip em data/`**: deixe apenas o zip da base na pasta.
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
├── notebooks/
│   └── validacao_tabelas.ipynb     # inspeção das 11 tabelas tratadas, em pandas
├── data/
│   ├── <base>.zip                  # zip da base, colocado por quem vai rodar
│   ├── extraido/                   # saída da extração, recriada a cada execução
│   └── tratados/                   # CSVs tratados, gerados pelo main.py
├── scripts/
│   └── gerar_imagens_relatorio.py  # exporta os gráficos usados no RELATORIO.md
├── docs/imagens/                   # gráficos do relatório, em PNG
├── src/
│   ├── extracao.py                 # localiza e descompacta o zip da base
│   ├── banco.py                    # classe BancoDados (conexão e queries)
│   ├── schema.sql                  # DDL: tabelas, PKs e FKs
│   ├── tratamentos/
│   │   ├── tratamento_tabelas.py   # tratamento de cada tabela
│   │   └── tratamento_utils.py     # utilitários de limpeza reutilizados
│   └── dashboard/
│       ├── querys/                 # um .sql por consulta, em SQL puro
│       │   ├── p1_taxa_aprovacao_por_ano.sql
│       │   ├── p2_aprovacao_por_faixa_de_presenca.sql
│       │   ├── p2_presenca_por_ano_e_situacao.sql
│       │   ├── p2_presenca_por_aluno.sql
│       │   ├── p2_estatisticas_presenca.sql
│       │   ├── p3_notas_por_materia_e_ano.sql
│       │   ├── p3_notas_por_materia_e_situacao.sql
│       │   ├── p3_aprovacoes_por_curso_e_ano.sql
│       │   ├── p3_notas_vestibular_por_curso.sql
│       │   ├── p3_notas_vestibular_por_ano.sql
│       │   ├── p3_simulado_vs_vestibular.sql
│       │   ├── p3_diferenca_simulado_vestibular_por_ano.sql
│       │   ├── p3_relacao_materia_e_curso.sql
│       │   ├── ex_professores_materias.sql
│       │   ├── ex_professores_desempenho.sql
│       │   ├── ex_modalidade_frequencia.sql
│       │   ├── ex_modalidade_aprovacao.sql
│       │   ├── ex_simulados_por_dispositivo.sql
│       │   ├── ex_simulados_por_unidade.sql
│       │   ├── ex_simulados_nota_por_tentativas.sql
│       │   └── p4_fatores_testados.sql
│       ├── dados.py                # lê e executa os .sql, com cache
│       ├── tema.py                 # paleta e especificações dos gráficos
│       ├── graficos.py             # formas reaproveitadas: mesma leitura, mesma forma
│       └── perguntas/              # uma página por análise
│           ├── p1_taxa_aprovacao.py
│           ├── p2_presenca_aprovacao.py
│           ├── p3_desempenho.py
│           ├── p4_recomendacoes.py
│           ├── extra_professores.py
│           ├── extra_modalidade.py
│           └── extra_simulados.py
└── RELATORIO.md                    # relatório final com as respostas e achados
```

## Etapas do pipeline

O `main.py` executa quatro etapas, nesta ordem:

1. **Extração** (`src/extracao.py`): localiza o único `.zip` em `data/`, descompacta
   em `data/extraido/` e devolve a pasta que contém os CSVs. A pasta de saída é
   recriada a cada execução, e metadados de compactação são descartados na extração.
2. **Tratamento** (`src/tratamentos/`): lê os CSVs e aplica limpeza, padronização e
   as regras de negócio, tabela por tabela.
3. **Carga** (`src/banco.py`): aplica o `schema.sql` e insere as tabelas via
   `COPY ... FROM STDIN`, respeitando a ordem de dependência das FKs.
4. **Exportação**: grava um CSV por tabela em `data/tratados/`.

## Dados tratados

Ao rodar o `main.py`, cada tabela final vai para `data/tratados/<tabela>.csv`, com
o conteúdo exatamente como ficou no banco: já com o tratamento, os filtros de FK e
os cadastros de estudante gerados na carga. É o artefato de base tratada, e fica
disponível mesmo sem subir o Postgres.

Para inspecionar as tabelas tratadas em pandas, sem banco e sem Docker:

```bash
pip install -r requirements.txt jupyterlab
jupyter lab notebooks/validacao_tabelas.ipynb
```

O notebook carrega as 11 tabelas finais por `main.carregar_base_tratada()`, o mesmo
caminho de código da carga no Postgres, e traz uma seção por tabela com os
tratamentos aplicados, checagens de PK/FK e comparações com a versão crua.

## Imagens do relatório

Os gráficos do [RELATORIO.md](RELATORIO.md) ficam em `docs/imagens/` e são gerados
pelas mesmas funções que desenham o dashboard, então imagem e tela não divergem. Para
regerar depois de uma nova carga:

```bash
pip install -r requirements.txt kaleido==0.2.1
python scripts/gerar_imagens_relatorio.py
```

## Consultas do dashboard

Cada análise do dashboard tem sua consulta num arquivo próprio em
`src/dashboard/querys/`, em **SQL puro e sem parâmetro**. A intenção é que a mesma
consulta que alimenta o gráfico possa ser aberta num cliente SQL (DBeaver) e
rodada sem adaptação — todo número do dashboard é conferível fora dele. O
`dados.py` só lê o arquivo e executa; quem define a métrica é o SQL.

Cada página traz também um expansor **"Ver o SQL desta análise"** com o texto da
consulta, para não ser preciso abrir o repositório para saber de onde saiu o número.

## Decisões técnicas relevantes

**Modelagem em Postgres com PK e FK.** A base foi modelada como um esquema
relacional (ver `src/schema.sql`). Ele tem uma dimensão de matérias (`dim_materia`)
gerada no tratamento e um relacionamento N:N `professor_materia`. Toda coluna que
referencia matéria usa o mesmo nome `materia_id`, para deixar explícito que é FK.

**A base entra por um zip, e a pasta dela é descoberta, não fixada.** Quem for rodar
só coloca o zip em `data/`. A extração procura, dentro do que foi descompactado, a
pasta que contém os CSVs esperados, então a estrutura interna do zip pode mudar sem
quebrar o pipeline. Os arquivos são lidos com `utf-8-sig` porque vêm com BOM: sem
isso a primeira coluna de cada tabela chegaria com um caractere invisível no nome.

**Carga via COPY.** Com a base completa são ~110 mil linhas no total, volume em
que o `INSERT` em lote leva minutos. A carga usa `COPY ... FROM STDIN` do
Postgres, e o pipeline inteiro (tratar, carregar e exportar) roda em poucos
segundos.

**Filtros de FK e estudantes stub como rede de proteção.** O `main.py` descarta
linhas com FK órfã e cria cadastros mínimos (stub, `nome_aluno = 'cadastro
ausente'`) para todo `aluno_id` que aparece nos fatos mas não no cadastro. Na base
atual isso nunca dispara: não há nenhuma FK órfã, os filtros descartam zero linha e
nenhum stub é criado. O código permanece porque é o que garante que a carga não
quebre caso a base chegue incompleta, e o log deixa explícito quando algo é
descartado.

**Tratamento centralizado e reutilizável.** O `tratamento_utils.py` concentra a
limpeza que se repetia célula a célula: normalização de texto, conversão de datas
em formatos mistos, tratamento de nulos disfarçados de string, criação de
dimensões e mapeamento de categoria para id.

**Escala de nota por matéria, e outliers capados em vez de descartados.** Redação é
corrigida em 0–1000 e as demais matérias em 0–100, então o teto da escala fica em
`dim_materia.nota_maxima`. A coluna `resultados_sim.nota_norm` traz a nota capada
nos limites da própria matéria e reescalada para 0–100 — é ela que torna as notas
comparáveis. Capar em vez de descartar preserva o registro do aluno sem deixar um
valor extremo inflar a média, e a nota original fica intacta ao lado das flags
`nota_acima_lim` e `nota_abaixo_lim`.

**Alinhamento por ano nos cruzamentos.** Sempre que uma análise cruza dois fatos
com data (matrícula e aprovação, simulado e vestibular, presença e aprovação), o
casamento é feito pelo mesmo ano. Isso evita comparar um evento de um ano com
outro de um ano diferente.

## Demonstração

O dashboard sobe junto com o `docker compose up` e fica em **http://localhost:8501**,
com uma página para cada pergunta do desafio, escolhida na barra lateral. Cada
página deixa o número de alunos à vista e traz o SQL que a alimenta.
