"""Tratamento de cada tabela da base pré-vestibular.

`tratar_professores` roda primeiro porque cria `dim_materia`, usada pelos demais.
`executar_pipeline()` chama tudo na ordem certa.
"""
import os

import numpy as np
import pandas as pd

from .tratamento_utils import TratamentoUtils

# Arquivo CSV de origem -> nome da tabela. Explícito porque dois nomes não batem:
# aprovacoes_vestibular.csv e resultados_simulados.csv.
ARQUIVOS_CSV = {
    "professores.csv": "professores",
    "estudantes.csv": "estudantes",
    "ofertas_curso.csv": "ofertas_curso",
    "matriculas.csv": "matriculas",
    "aprovacoes_vestibular.csv": "aprovacoes",
    "simulados.csv": "simulados",
    "resultados_simulados.csv": "resultados_sim",
    "aulas.csv": "aulas",
    "presencas_aulas.csv": "presencas_aulas",
}

# Teto da escala de correção por matéria. Redação é corrigida em 0-1000 e as
# demais em 0-100.
NOTA_MAXIMA_PADRAO = 100
NOTA_MAXIMA_POR_MATERIA = {"redacao": 1000}

# Tolerância de atraso em minutos: quem compareceu com atraso acima deste valor é
# classificado como 'atrasado'. 0 significa que qualquer minuto conta como atraso.
# Mudar aqui altera só a fronteira entre 'presente' e 'atrasado'.
TOLERANCIA_ATRASO_MIN = 0


class TratamentoTabelas:
    """Carrega e trata as tabelas da base pré-vestibular."""

    def __init__(
        self,
        diretorio_csv: str | None = None,
        tabelas: dict[str, pd.DataFrame] | None = None,
    ):
        """Inicializa a classe a partir dos CSVs de origem ou de tabelas em memória.

        Args:
            diretorio_csv: diretório com os CSVs da base.
            tabelas: dicionário {nome_tabela: DataFrame} já carregado, usado no
                lugar da leitura de arquivo (útil em testes). Tem precedência.
        """
        self.utils = TratamentoUtils

        if tabelas is not None:
            self.tabelas = tabelas
        elif diretorio_csv is not None:
            self.tabelas = self.carregar_dados_csv(diretorio_csv)
        else:
            self.tabelas = {}

        # Dimensões e relacionamentos gerados durante os tratamentos
        self.dim_materia: pd.DataFrame | None = None
        self.professor_materia: pd.DataFrame | None = None

    # Leitura
    def carregar_dados_csv(self, diretorio: str) -> dict[str, pd.DataFrame]:
        """Lê os CSVs da base.

        Args:
            diretorio: pasta com os CSVs.

        Returns:
            Dicionário {nome_tabela: DataFrame} com os dados crus.

        Raises:
            FileNotFoundError: se algum CSV esperado não estiver no diretório.
        """
        tabelas = {}
        for arquivo, chave in ARQUIVOS_CSV.items():
            caminho = os.path.join(diretorio, arquivo)
            if not os.path.exists(caminho):
                raise FileNotFoundError(
                    f"CSV da base completa não encontrado: {caminho}"
                )
            df = pd.read_csv(caminho, encoding="utf-8-sig")
            tabelas[chave] = df
            print(f"{chave} -> {df.shape}")

        return tabelas

    # professores
    def tratar_professores(self) -> pd.DataFrame:
        """Trata professores e gera `dim_materia` e `professor_materia`.

        Returns:
            O DataFrame de professores tratado.
        """
        df = self.tabelas['professores'].copy()

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
        # A escala da nota é atributo da matéria, então mora na dimensão: assim
        # tratamento e dashboard leem a mesma fonte, em vez de repetir o limite
        # em cada consulta.
        self.dim_materia['nota_maxima'] = (
            self.dim_materia['nome_materia']
            .map(NOTA_MAXIMA_POR_MATERIA)
            .fillna(NOTA_MAXIMA_PADRAO)
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

        self.tabelas['professores'] = df
        return df

    # estudantes
    def tratar_estudantes(self) -> pd.DataFrame:
        """Trata estudantes: nulos, texto, datas e pontuação de telefone e CPF.

        Returns:
            O DataFrame de estudantes tratado.
        """
        df = self.tabelas['estudantes'].copy()

        df['escola_origem'] = self.utils.preencher_nulos(df['escola_origem'], 'Não informado')
        df = self.utils.normalizar_colunas(df, ['escola_origem', 'cidade', 'canal_captacao'])

        for coluna in ['data_cadastro', 'data_nascimento']:
            df[coluna] = self.utils.tratar_data(df[coluna])

        df['telefone'] = self.utils.limpar_pontuacao(df['telefone'], r'[()\-\s]')
        df['cpf_ficticio'] = self.utils.limpar_pontuacao(df['cpf_ficticio'], r'[.\-]')

        for coluna in ['cpf_ficticio', 'email_aluno', 'telefone', 'canal_captacao']:
            df[coluna] = self.utils.preencher_nulos(df[coluna], 'sem registro')

        self.tabelas['estudantes'] = df
        return df

    # ofertas_curso
    def tratar_ofertas_curso(self) -> pd.DataFrame:
        """Trata ofertas de curso: datas e matéria trocada pelo id.

        Returns:
            O DataFrame de ofertas tratado.

        Raises:
            RuntimeError: se `tratar_professores()` não rodou antes.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['ofertas_curso'].copy()
        df = df.drop(columns=['professor_nome_informado'])

        for coluna in ['data_inicio', 'data_fim']:
            df[coluna] = self.utils.tratar_data(df[coluna])

        df = self.utils.normalizar_colunas(df, ['materia'])
        df['materia'] = self.utils.mapear_para_id(df['materia'], self.dim_materia, 'nome_materia', 'materia_id')
        df = df.rename(columns={'materia': 'materia_id'})

        self.tabelas['ofertas_curso'] = df
        return df

    # matriculas
    def tratar_matriculas(self) -> pd.DataFrame:
        """Trata matrículas: numéricos, datas, texto e matéria trocada pelo id.

        Returns:
            O DataFrame de matrículas tratado.

        Raises:
            RuntimeError: se `tratar_professores()` não rodou antes.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['matriculas'].copy()

        for coluna in ['bolsa_percentual', 'nota_diagnostico']:
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

        self.tabelas['matriculas'] = df
        return df

    # simulados
    def tratar_simulados(self) -> pd.DataFrame:
        """Trata simulados: nulos, texto, datas e matéria trocada pelo id.

        Returns:
            O DataFrame de simulados tratado.

        Raises:
            RuntimeError: se `tratar_professores()` não rodou antes.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['simulados'].copy()

        df['tema'] = self.utils.preencher_nulos(df['tema'], 'nao informado')
        df['dificuldade'] = self.utils.preencher_nulos(df['dificuldade'], 'nao informado')
        df = self.utils.normalizar_colunas(df, ['tema', 'dificuldade', 'materia', 'tipo_simulado'])
        df['materia'] = df['materia'].replace({'mat.': 'matematica'})
        df['data_simulado'] = self.utils.tratar_data(df['data_simulado'])
        df['materia'] = self.utils.mapear_para_id(df['materia'], self.dim_materia, 'nome_materia', 'materia_id')
        df = df.rename(columns={'materia': 'materia_id'})
        df = df.drop(columns=['professor_nome_informado'])

        self.tabelas['simulados'] = df
        return df

    # resultados_sim
    def tratar_resultados_sim(self) -> pd.DataFrame:
        """Trata a tabela de resultados de simulado.

        Preenche nulos, converte campos numéricos e de data, e sinaliza
        três tipos de outlier: nota acima da escala da matéria, nota
        negativa e tempo de finalização acima do `tempo_limite_min` do
        simulado correspondente. Os valores originais não são corrigidos,
        apenas sinalizados em `nota_acima_lim`, `nota_abaixo_lim` e
        `tempo_acima_lim`.

        Gera também `nota_norm`, a nota capada nos limites da matéria e
        reescalada para 0-100. Como redação é corrigida em 0-1000 e as
        demais matérias em 0-100, é essa coluna que torna as notas
        comparáveis entre matérias.

        Returns:
            O DataFrame de resultados de simulado já tratado.

        Raises:
            RuntimeError: se `tratar_professores()` ainda não rodou.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['resultados_sim'].copy()

        # Padroniza caixa/acentos das colunas categóricas antes de preencher nulos
        df = self.utils.normalizar_colunas(
            df, ['status_realizacao', 'dispositivo', 'unidade_aplicacao']
        )

        df['status_realizacao'] = self.utils.preencher_nulos(df['status_realizacao'], 'status ausente')
        df['dispositivo'] = self.utils.preencher_nulos(df['dispositivo'], 'sem registro')
        df['unidade_aplicacao'] = self.utils.preencher_nulos(df['unidade_aplicacao'], 'sem registro')

        df['nota'] = self.utils.tratar_numerico(df['nota'], valor_padrao=0)
        # acertos fica sem preenchimento: em redação a coluna é 100% nula (a
        # matéria não tem questões objetivas), e preencher com 0 faria a média
        # de acertos da matéria aparecer como 0 no dashboard, um número que
        # nunca foi medido. Nulo aqui significa "não se aplica/não registrado".
        df['acertos'] = pd.to_numeric(
            self.utils.limpar_nulos_textuais(df['acertos']), errors='coerce'
        )
        df['tempo_finalizacao_min'] = self.utils.tratar_numerico(df['tempo_finalizacao_min'], valor_padrao=0)
        df['tentativas'] = self.utils.tratar_numerico(df['tentativas'], valor_padrao=0)

        # inicio_simulado mistura "28/05/2021 12:00" e "2021-10-10 10:00":
        # tratar_data detecta o ':' e já formata como data + hora
        df['inicio_simulado'] = self.utils.tratar_data(df['inicio_simulado'])

        # Outlier 1: nota fora da escala da própria matéria. O limite superior
        # vem de dim_materia (100 na maioria, 1000 em redação) e o inferior é
        # sempre 0. Não corrigimos o valor original (pode ser erro de digitação
        # ou de fonte), só sinalizamos e guardamos a versão normalizada.
        materias = self.tabelas['simulados'][['simulado_id', 'materia_id']]
        df = df.merge(materias, on='simulado_id', how='left')
        df['nota_maxima'] = self.utils.mapear_para_id(
            df['materia_id'], self.dim_materia, 'materia_id', 'nota_maxima'
        )

        df['nota_acima_lim'] = df['nota'] > df['nota_maxima']
        df['nota_abaixo_lim'] = df['nota'] < 0

        # nota_norm põe todas as matérias na mesma escala 0-100, capando os
        # outliers nas duas pontas. É essa coluna que as análises usam, para
        # não repetir a regra de escala em cada consulta.
        df['nota_norm'] = (
            df['nota'].clip(lower=0).clip(upper=df['nota_maxima'])
            / df['nota_maxima'] * 100
        ).round(1)
        df = df.drop(columns=['materia_id', 'nota_maxima'])

        # Outlier 2: tempo de finalização acima do tempo_limite_min do próprio
        # simulado (tabela simulados). Usamos a tabela ainda "crua"
        # (chave/tempo não sofrem tratamento de texto) só para essa checagem.
        limites = self.tabelas['simulados'][['simulado_id', 'tempo_limite_min']]
        df = df.merge(limites, on='simulado_id', how='left')
        df['tempo_acima_lim'] = df['tempo_finalizacao_min'] > df['tempo_limite_min']
        df = df.drop(columns=['tempo_limite_min'])

        self.tabelas['resultados_sim'] = df
        return df

    # aulas
    def tratar_aulas(self) -> pd.DataFrame:
        """Trata aulas: texto, nulos, numéricos, datas e matéria trocada pelo id.

        Returns:
            O DataFrame de aulas tratado.

        Raises:
            RuntimeError: se `tratar_professores()` não rodou antes.
        """
        if self.dim_materia is None:
            raise RuntimeError("Rode tratar_professores() antes: dim_materia ainda não existe.")

        df = self.tabelas['aulas'].copy()

        df = self.utils.normalizar_colunas(df, ['modalidade_aula', 'materia', 'tema_aula'])
        df['modalidade_aula'] = self.utils.preencher_nulos(df['modalidade_aula'], 'sem registro')

        df['duracao_min'] = self.utils.tratar_numerico(df['duracao_min'], valor_padrao=0)
        df['data_aula'] = self.utils.tratar_data(df['data_aula'])
        df['materia'] = self.utils.mapear_para_id(df['materia'], self.dim_materia, 'nome_materia', 'materia_id')
        df = df.rename(columns={'materia': 'materia_id'})

        self.tabelas['aulas'] = df
        return df

    # presencas_aulas
    def tratar_presencas_aulas(self) -> pd.DataFrame:
        """Trata a tabela de presenças em aula.

        Normaliza o status de presença e aplica duas regras de negócio:

        1. Ausência com justificativa preenchida vira "justificado". Nulos
           em `justificativa` são mantidos como estão (ausência de
           justificativa é um estado válido).
        2. Entre quem compareceu, o status é **reconciliado com o atraso
           medido**: atraso acima de `TOLERANCIA_ATRASO_MIN` é "atrasado",
           até a tolerância é "presente". A origem traz os dois campos
           preenchidos de forma independente (`presente` e `atrasado` têm
           distribuição de `atraso_min` idêntica, e 33 mil registros
           `presente` têm atraso acima de zero), então o rótulo original
           não é confiável. `atraso_min` é a medida, e é ela que decide.

        Quando `atraso_min` é nulo não há medida para reconciliar, e o
        status original é mantido: nulo aqui significa "não registrado", ou
        "não se aplica" no caso de quem não compareceu.

        Returns:
            O DataFrame de presenças já tratado.
        """
        df = self.tabelas['presencas_aulas'].copy()

        df = self.utils.normalizar_colunas(df, ['status_presenca'])

        # atraso_min preserva o nulo, em vez de virar 0: "chegou na hora" (0) e
        # "atraso não registrado" (nulo) são coisas diferentes, e a distinção é o
        # que decide se há medida para reconciliar o status. Só quem compareceu
        # tem atraso: em `ausente` e `justificado` a coluna é 100% nula na origem,
        # e preencher com 0 afirmaria que o aluno faltante chegou na hora.
        df['atraso_min'] = pd.to_numeric(
            self.utils.limpar_nulos_textuais(df['atraso_min']), errors='coerce'
        )

        # Regra de negócio 1: ausente com justificativa preenchida vira "justificado"
        mask_ausente_justificado = (df['status_presenca'] == 'ausente') & df['justificativa'].notna()
        df.loc[mask_ausente_justificado, 'status_presenca'] = 'justificado'

        # Regra de negócio 2: reconcilia o status de quem compareceu com o atraso
        # medido. Não altera nenhuma taxa de frequência, porque as análises somam
        # 'presente' e 'atrasado' como comparecimento, mas faz a categoria
        # 'atrasado' passar a significar algo.
        compareceu = df['status_presenca'].isin(['presente', 'atrasado'])
        tem_medida = df['atraso_min'].notna()
        df.loc[compareceu & tem_medida, 'status_presenca'] = np.where(
            df.loc[compareceu & tem_medida, 'atraso_min'] > TOLERANCIA_ATRASO_MIN,
            'atrasado',
            'presente',
        )

        df['status_presenca'] = self.utils.preencher_nulos(df['status_presenca'], 'sem registro')
        # justificativa: mantida como está, nulos são um estado válido (sem justificativa)

        self.tabelas['presencas_aulas'] = df
        return df

    # aprovacoes
    def tratar_aprovacoes(self) -> pd.DataFrame:
        """Trata aprovações e remove as duplicadas por regra de negócio.

        Returns:
            O DataFrame de aprovações tratado.
        """
        df = self.tabelas['aprovacoes'].copy()

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

        self.tabelas['aprovacoes'] = df
        return df

    # Pipeline completo
    def executar_pipeline(self) -> dict[str, pd.DataFrame]:
        """Roda todos os tratamentos na ordem de dependência.

        Returns:
            Dicionário {nome_tabela: DataFrame} com todas as tabelas tratadas.
        """
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