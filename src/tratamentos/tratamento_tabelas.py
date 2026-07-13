"""
Classe responsável pelos tratamentos de cada tabela da base pré-vestibular.

Cada método `tratar_*` corresponde a uma seção do notebook de exploração
original. A ordem importa: `tratar_professores` precisa rodar primeiro
porque cria a dimensão `dim_materia`, usada por `tratar_ofertas_curso` e
`tratar_matriculas`. Use `executar_pipeline()` para rodar tudo na ordem
correta de uma vez.
"""
import pandas as pd

from .tratamento_utils import TratamentoUtils


class TratamentoTabelas:
    """Carrega e trata as tabelas da base pré-vestibular."""

    def __init__(self, arquivo: str | None = None, tabelas: dict[str, pd.DataFrame] | None = None):
        """Inicializa a classe a partir de um arquivo Excel ou de tabelas já em memória.

        Args:
            arquivo: caminho do Excel com as abas de amostra. Ignorado se
                `tabelas` for informado.
            tabelas: dicionário {nome_tabela: DataFrame} já carregado,
                usado no lugar da leitura do Excel (útil em testes).
        """
        self.utils = TratamentoUtils

        if tabelas is not None:
            self.tabelas = tabelas
        elif arquivo is not None:
            self.tabelas = self.carregar_dados(arquivo)
        else:
            self.tabelas = {}

        # Dimensões e relacionamentos gerados durante os tratamentos
        self.dim_materia: pd.DataFrame | None = None
        self.professor_materia: pd.DataFrame | None = None

    # Leitura
    def carregar_dados(self, arquivo: str) -> dict[str, pd.DataFrame]:
        """Lê todas as abas do excel e padroniza os nomes (chaves do dict)
        para snake_case."""
        tabelas_brutas = pd.read_excel(arquivo, sheet_name=None)

        tabelas = {}
        for nome, df in tabelas_brutas.items():
            var_name = self.utils.to_snake_case(nome)
            tabelas[var_name] = df
            print(f"{var_name} -> {df.shape}")

        return tabelas

    # amostra_professores
    def tratar_professores(self) -> pd.DataFrame:
        """Trata a tabela de professores.

        Preenche nulos, normaliza texto e datas, e gera dois artefatos
        usados pelos demais tratamentos: a dimensão `dim_materia` e o
        relacionamento N:N `professor_materia`. Também remove o cadastro
        duplicado de professor (mesmo `nome_professor` com `professor_id`
        diferente), mantendo a primeira ocorrência.

        Returns:
            O DataFrame de professores já tratado.
        """
        df = self.tabelas['amostra_professores'].copy()

        df['observacoes'] = self.utils.preencher_nulos(df['observacoes'], 'sem observacoes')
        df['email_professor'] = self.utils.preencher_nulos(df['email_professor'], 'sem registro')
        df['carga_horaria_semanal'] = self.utils.tratar_numerico(df['carga_horaria_semanal'])
        df['data_contratacao'] = self.utils.tratar_data(df['data_contratacao'])

        df = self.utils.normalizar_colunas(
            df, ['status_professor', 'unidade_base', 'materia_principal']
        )
        df['materia_principal'] = df['materia_principal'].replace({'mat.': 'matematica'})

        # Remove o cadastro duplicado (mesmo nome_professor, professor_id
        # diferente) antes de gerar dim_materia e o relacionamento N:N.
        # Assim nenhum dos dois artefatos carrega um professor_id que não
        # sobrevive na tabela final de professores.
        df = df.drop_duplicates(subset='nome_professor', keep='first').reset_index(drop=True)

        # Dimensão de matérias, usada também por ofertas_curso e matriculas
        self.dim_materia = self.utils.criar_dimensao(
            df['materia_principal'], nome_coluna_valor='nome_materia', nome_coluna_id='materia_id'
        )

        # Relacionamento professor <-> matéria (N:N), antes de descartar a coluna original
        relacao = self.utils.explodir_coluna(
            df, colunas_manter=['professor_id'], coluna_explodir='materias_ensina', separador=';'
        )
        relacao['materias_ensina'] = (
            relacao['materias_ensina']
            .map(self.utils.normalizar_texto)
            .replace({'mat.': 'matematica'})
        )
        relacao['materia_id'] = self.utils.mapear_para_id(
            relacao['materias_ensina'], self.dim_materia, 'nome_materia', 'materia_id'
        )
        self.professor_materia = (
            relacao[['professor_id', 'materia_id']]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        # Substitui o nome da matéria principal pelo id e remove a coluna N:N
        df['materia_principal'] = self.utils.mapear_para_id(
            df['materia_principal'], self.dim_materia, 'nome_materia', 'materia_id'
        )
        df = df.rename(columns={'materia_principal': 'materia_id'})
        df = df.drop(columns=['materias_ensina'])

        self.tabelas['amostra_professores'] = df
        return df

    # amostra_estudantes
    def tratar_estudantes(self) -> pd.DataFrame:
        """Trata a tabela de estudantes.

        Preenche nulos textuais, normaliza colunas categóricas, converte
        datas e remove pontuação de telefone e CPF fictício.

        Returns:
            O DataFrame de estudantes já tratado.
        """
        df = self.tabelas['amostra_estudantes'].copy()

        df['escola_origem'] = self.utils.preencher_nulos(df['escola_origem'], 'Não informado')
        df = self.utils.normalizar_colunas(df, ['escola_origem', 'cidade', 'canal_captacao'])

        for coluna in ['data_cadastro', 'data_nascimento']:
            df[coluna] = self.utils.tratar_data(df[coluna])

        df['telefone'] = self.utils.limpar_pontuacao(df['telefone'], r'[()\-\s]')
        df['cpf_ficticio'] = self.utils.limpar_pontuacao(df['cpf_ficticio'], r'[.\-]')

        for coluna in ['cpf_ficticio', 'email_aluno', 'telefone', 'canal_captacao']:
            df[coluna] = self.utils.preencher_nulos(df[coluna], 'sem registro')

        self.tabelas['amostra_estudantes'] = df
        return df

    # amostra_ofertas_curso
    def tratar_ofertas_curso(self) -> pd.DataFrame:
        """Trata a tabela de ofertas de curso.

        Remove a coluna de nome de professor informado manualmente,
        converte datas e substitui o nome da matéria pelo id em
        `dim_materia`.

        Returns:
            O DataFrame de ofertas de curso já tratado.

        Raises:
            RuntimeError: se `tratar_professores()` ainda não rodou.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['amostra_ofertas_curso'].copy()
        df = df.drop(columns=['professor_nome_informado'])

        for coluna in ['data_inicio', 'data_fim']:
            df[coluna] = self.utils.tratar_data(df[coluna])

        df = self.utils.normalizar_colunas(df, ['materia'])
        df['materia'] = self.utils.mapear_para_id(df['materia'], self.dim_materia, 'nome_materia', 'materia_id')
        df = df.rename(columns={'materia': 'materia_id'})

        self.tabelas['amostra_ofertas_curso'] = df
        return df

    # amostra_matriculas
    def tratar_matriculas(self) -> pd.DataFrame:
        """Trata a tabela de matrículas.

        Converte campos numéricos e de data, normaliza colunas
        categóricas e substitui a matéria declarada pelo id em
        `dim_materia`.

        Returns:
            O DataFrame de matrículas já tratado.

        Raises:
            RuntimeError: se `tratar_professores()` ainda não rodou.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['amostra_matriculas'].copy()

        for coluna in ['bolsa_percentual', 'nota_diagnóstico']:
            if coluna in df.columns:
                df[coluna] = self.utils.tratar_numerico(df[coluna])

        df['data_matricula'] = self.utils.tratar_data(df['data_matricula'])
        df = self.utils.normalizar_colunas(df, ['status_matricula', 'materia_declarada', 'origem_captacao'])
        df['materia_declarada'] = df['materia_declarada'].replace({'mat.': 'matematica'})
        df['status_matricula'] = self.utils.preencher_nulos(df['status_matricula'], 'sem status')
        df['origem_captacao'] = self.utils.preencher_nulos(df['origem_captacao'], 'sem registro')
        df['materia_declarada'] = self.utils.mapear_para_id(
            df['materia_declarada'], self.dim_materia, 'nome_materia', 'materia_id'
        )
        df = df.rename(columns={'materia_declarada': 'materia_id'})

        self.tabelas['amostra_matriculas'] = df
        return df

    # amostra_simulados
    def tratar_simulados(self) -> pd.DataFrame:
        """Trata a tabela de simulados.

        Preenche nulos textuais, normaliza colunas categóricas, converte
        datas, substitui a matéria pelo id em `dim_materia` e remove a
        coluna de nome de professor informado manualmente.

        Returns:
            O DataFrame de simulados já tratado.

        Raises:
            RuntimeError: se `tratar_professores()` ainda não rodou.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['amostra_simulados'].copy()

        df['tema'] = self.utils.preencher_nulos(df['tema'], 'nao informado')
        df['dificuldade'] = self.utils.preencher_nulos(df['dificuldade'], 'nao informado')
        df = self.utils.normalizar_colunas(df, ['tema', 'dificuldade', 'materia', 'tipo_simulado'])
        df['materia'] = df['materia'].replace({'mat.': 'matematica'})
        df['data_simulado'] = self.utils.tratar_data(df['data_simulado'])
        df['materia'] = self.utils.mapear_para_id(df['materia'], self.dim_materia, 'nome_materia', 'materia_id')
        df = df.rename(columns={'materia': 'materia_id'})
        df = df.drop(columns=['professor_nome_informado'])

        self.tabelas['amostra_simulados'] = df
        return df

    # amostra_resultados_sim
    def tratar_resultados_sim(self) -> pd.DataFrame:
        """Trata a tabela de resultados de simulado.

        Preenche nulos, converte campos numéricos e de data, e sinaliza
        dois tipos de outlier: nota acima da escala plausível (0-100) e
        tempo de finalização acima do `tempo_limite_min` do simulado
        correspondente. Os valores não são corrigidos, apenas sinalizados
        nas colunas `nota_acima_lim` e `tempo_acima_lim`.

        Returns:
            O DataFrame de resultados de simulado já tratado.
        """
        df = self.tabelas['amostra_resultados_sim'].copy()

        # Padroniza caixa/acentos das colunas categóricas antes de preencher nulos
        df = self.utils.normalizar_colunas(
            df, ['status_realizacao', 'dispositivo', 'unidade_aplicacao']
        )

        df['status_realizacao'] = self.utils.preencher_nulos(df['status_realizacao'], 'status ausente')
        df['dispositivo'] = self.utils.preencher_nulos(df['dispositivo'], 'sem registro')
        df['unidade_aplicacao'] = self.utils.preencher_nulos(df['unidade_aplicacao'], 'sem registro')

        df['nota'] = self.utils.tratar_numerico(df['nota'], valor_padrao=0)
        df['acertos'] = self.utils.tratar_numerico(df['acertos'], valor_padrao=0)
        df['tempo_finalizacao_min'] = self.utils.tratar_numerico(df['tempo_finalizacao_min'], valor_padrao=0)
        df['tentativas'] = self.utils.tratar_numerico(df['tentativas'], valor_padrao=0)

        # inicio_simulado mistura "28/05/2021 12:00" e "2021-10-10 10:00":
        # tratar_data detecta o ':' e já formata como data + hora
        df['inicio_simulado'] = self.utils.tratar_data(df['inicio_simulado'])

        # Outlier 1: nota acima da escala plausível (0-100). Não corrigimos o
        # valor (pode ser erro de digitação ou de fonte), só sinalizamos.
        df['nota_acima_lim'] = df['nota'] > 100

        # Outlier 2: tempo de finalização acima do tempo_limite_min do próprio
        # simulado (tabela amostra_simulados). Usamos a tabela ainda "crua"
        # (chave/tempo não sofrem tratamento de texto) só para essa checagem.
        limites = self.tabelas['amostra_simulados'][['simulado_id', 'tempo_limite_min']]
        df = df.merge(limites, on='simulado_id', how='left')
        df['tempo_acima_lim'] = df['tempo_finalizacao_min'] > df['tempo_limite_min']
        df = df.drop(columns=['tempo_limite_min'])

        self.tabelas['amostra_resultados_sim'] = df
        return df

    # amostra_aulas
    def tratar_aulas(self) -> pd.DataFrame:
        """Trata a tabela de aulas.

        Normaliza colunas categóricas, preenche nulos, converte campos
        numéricos e de data, e substitui a matéria pelo id em
        `dim_materia`.

        Returns:
            O DataFrame de aulas já tratado.

        Raises:
            RuntimeError: se `tratar_professores()` ainda não rodou.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['amostra_aulas'].copy()

        df = self.utils.normalizar_colunas(df, ['modalidade_aula', 'materia', 'tema_aula'])
        df['modalidade_aula'] = self.utils.preencher_nulos(df['modalidade_aula'], 'sem registro')

        df['duracao_min'] = self.utils.tratar_numerico(df['duracao_min'], valor_padrao=0)
        df['data_aula'] = self.utils.tratar_data(df['data_aula'])
        df['materia'] = self.utils.mapear_para_id(df['materia'], self.dim_materia, 'nome_materia', 'materia_id')
        df = df.rename(columns={'materia': 'materia_id'})

        self.tabelas['amostra_aulas'] = df
        return df

    # amostra_presencas_aulas
    def tratar_presencas_aulas(self) -> pd.DataFrame:
        """Trata a tabela de presenças em aula.

        Normaliza o status de presença e aplica a regra de negócio: uma
        ausência com justificativa preenchida vira "justificado". Nulos
        em `justificativa` são mantidos como estão (ausência de
        justificativa é um estado válido).

        Returns:
            O DataFrame de presenças já tratado.
        """
        df = self.tabelas['amostra_presencas_aulas'].copy()

        df = self.utils.normalizar_colunas(df, ['status_presenca'])

        # Regra de negócio: ausente com justificativa preenchida vira "justificado"
        mask_ausente_justificado = (df['status_presenca'] == 'ausente') & df['justificativa'].notna()
        df.loc[mask_ausente_justificado, 'status_presenca'] = 'justificado'

        df['status_presenca'] = self.utils.preencher_nulos(df['status_presenca'], 'sem registro')
        df['atraso_min'] = self.utils.tratar_numerico(df['atraso_min'], valor_padrao=0)
        # justificativa: mantida como está, nulos são um estado válido (sem justificativa)

        self.tabelas['amostra_presencas_aulas'] = df
        return df

    # amostra_aprovacoes
    def tratar_aprovacoes(self) -> pd.DataFrame:
        """Trata a tabela de aprovações.

        Normaliza colunas categóricas, converte a data de resultado e
        remove cadastros duplicados: quando a mesma combinação de
        aluno/ano/universidade/curso aparece duas vezes, mantém a linha
        com a chamada real e descarta a marcada como
        "cadastro duplicado?".

        Returns:
            O DataFrame de aprovações já tratado.
        """
        df = self.tabelas['amostra_aprovacoes'].copy()

        df = self.utils.normalizar_colunas(
            df, ['universidade', 'curso_aprovado', 'modalidade_vaga', 'chamada', 'bolsa_aprovacao', 'campus']
        )
        df['data_resultado'] = self.utils.tratar_data(df['data_resultado'])

        df['campus'] = self.utils.preencher_nulos(df['campus'], 'nao informado')
        df['chamada'] = self.utils.preencher_nulos(df['chamada'], 'nao informado')
        df['bolsa_aprovacao'] = self.utils.preencher_nulos(df['bolsa_aprovacao'], 'nao informado')
        df['modalidade_vaga'] = self.utils.preencher_nulos(df['modalidade_vaga'], 'nao informado')

        # Regra de negócio para duplicidade: um mesmo aluno pode ter mais de uma
        # aprovação legítima (anos/universidades diferentes), então dropar por
        # aluno_id sozinho apaga aprovações válidas. O problema real é marcado
        # em chamada == 'cadastro duplicado?': quando a mesma combinação de
        # aluno/ano/universidade/curso aparece duas vezes, uma das linhas traz
        # esse marcador e é ela que deve sair, mantendo a linha com a chamada real.
        df = df.sort_values('chamada', key=lambda s: s.eq('cadastro duplicado?'), kind='stable')
        df = df.drop_duplicates(
            subset=['aluno_id', 'ano_vestibular', 'universidade', 'curso_aprovado'], keep='first'
        ).reset_index(drop=True)

        self.tabelas['amostra_aprovacoes'] = df
        return df

    # Pipeline completo
    def executar_pipeline(self) -> dict[str, pd.DataFrame]:
        """Roda os tratamentos já finalizados, na ordem correta de dependência."""
        self.tratar_professores()
        self.tratar_estudantes()
        self.tratar_ofertas_curso()
        self.tratar_matriculas()
        self.tratar_simulados()
        self.tratar_resultados_sim()
        self.tratar_aulas()
        self.tratar_presencas_aulas()
        self.tratar_aprovacoes()
        return self.tabelas