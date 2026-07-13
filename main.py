"""
Ponto de entrada do projeto: cria o schema do banco "desafio_logap" e
carrega nele as tabelas tratadas a partir do Excel de amostras.

A conexão é sempre encerrada no `finally`, mesmo que a criação do schema
ou a carga de alguma tabela falhe no meio do caminho.
"""

import os

import numpy as np
import pandas as pd

from src.banco import BancoDados
from src.tratamentos.tratamento_tabelas import TratamentoTabelas

ARQUIVO_EXCEL = os.path.join(
    os.path.dirname(__file__), "data", "base_pre_vestibular_dicionario_amostras.xlsx"
)

DIRETORIO_TRATADOS = os.path.join(os.path.dirname(__file__), "data", "tratados")

# Tabelas exportadas para CSV ao fim da carga, na ordem de dependência.
TABELAS_EXPORTAR = [
    "dim_materia",
    "professores",
    "professor_materia",
    "estudantes",
    "ofertas_curso",
    "matriculas",
    "aprovacoes",
    "simulados",
    "resultados_sim",
    "aulas",
    "presencas_aulas",
]


def limpar_nat(df: pd.DataFrame) -> pd.DataFrame:
    """Converte strings literais 'NaT' em nulo antes da carga no banco.

    `TratamentoUtils.tratar_data()` faz `strftime` em cima de valores
    nulos de data, o que gera a string literal 'NaT' em vez de um nulo de
    fato. Colunas DATE/TIMESTAMP no Postgres não aceitam essa string.

    Args:
        df: DataFrame já tratado, pronto para ir ao banco.

    Returns:
        O mesmo DataFrame com ocorrências de 'NaT' substituídas por NaN.
    """
    return df.replace({"NaT": np.nan, "NaT NaT": np.nan})


def filtrar_fk_valida(
    df: pd.DataFrame, coluna: str, valores_validos: set, nome_tabela: str
) -> pd.DataFrame:
    """Remove linhas cuja FK não existe na tabela referenciadas.

    Args:
        df: DataFrame a filtrar.
        coluna: nome da coluna de FK.
        valores_validos: conjunto de chaves válidas na tabela referenciada.
        nome_tabela: nome da tabela, usado só para o log.

    Returns:
        O DataFrame sem as linhas com FK órfã.
    """
    if coluna not in df.columns:
        return df

    mask_valida = df[coluna].isna() | df[coluna].isin(valores_validos)
    n_orfas = (~mask_valida).sum()
    if n_orfas:
        pct = 100 * n_orfas / len(df)
        print(
            f"  [!] {nome_tabela}: {n_orfas}/{len(df)} linhas ({pct:.1f}%) com "
            f"'{coluna}' que não existe na tabela referenciada, descartadas."
        )
    return df[mask_valida].copy()


def adicionar_estudantes_stub(
    estudantes: pd.DataFrame, tabelas_fato: list[pd.DataFrame]
) -> pd.DataFrame:
    """Cria cadastros mínimos (stub) para aluno_id presentes nos fatos mas não no cadastro.

    A amostra de `estudantes` cobre só parte dos alunos (500 de 812), então
    aprovações, presenças e resultados de simulado de um aluno fora dessa
    fatia seriam descartados na carga pela FK com `estudantes`, perdendo
    dado linkável (o mesmo aluno tem aprovação e presença na amostra, mas
    não sobrevive porque falta o cadastro). Para preservá-los, cada
    `aluno_id` órfão referenciado em algum fato entra em `estudantes` como
    cadastro mínimo (só o id + um nome placeholder), mantendo a integridade
    referencial do schema.

    Args:
        estudantes: DataFrame de estudantes já tratado.
        tabelas_fato: DataFrames de fato que têm coluna `aluno_id`.

    Returns:
        O DataFrame de estudantes com os stubs concatenados.
    """
    existentes = set(estudantes["aluno_id"])
    referenciados: set = set()
    for df in tabelas_fato:
        if "aluno_id" in df.columns:
            referenciados |= set(df["aluno_id"].dropna())

    orfaos = sorted(referenciados - existentes)
    if not orfaos:
        return estudantes

    stubs = pd.DataFrame({"aluno_id": orfaos, "nome_aluno": "cadastro ausente"})
    print(
        f"  [i] estudantes: {len(orfaos)} aluno_id referenciados nos fatos não "
        "estavam no cadastro amostrado, adicionados como stub para preservar "
        "as linhas linkáveis."
    )
    return pd.concat([estudantes, stubs], ignore_index=True)


def exportar_tratados(banco: BancoDados, destino: str = DIRETORIO_TRATADOS) -> None:
    """Exporta cada tabela final do banco para um CSV em `destino`.

    Gera o artefato tangível de "dados tratados": um CSV por tabela, com o
    conteúdo exatamente como ficou no banco, ou seja, já com o tratamento,
    os filtros de FK e os stubs de estudante aplicados. Assim o avaliador
    tem a base tratada mesmo sem subir o Postgres.

    Args:
        banco: conexão já aberta com o banco.
        destino: diretório onde os CSVs são gravados (criado se não existir).
    """
    os.makedirs(destino, exist_ok=True)
    for tabela in TABELAS_EXPORTAR:
        df = banco.consultar(f"SELECT * FROM {tabela}")
        df.to_csv(os.path.join(destino, f"{tabela}.csv"), index=False)
        print(f"  -> {tabela}.csv ({len(df)} linhas)")


def main() -> None:
    """Cria o schema e carrega as tabelas tratadas no banco desafio_logap."""
    banco = BancoDados()
    try:
        banco.conectar()
        banco.criar_db()

        print("\nRodando pipeline de tratamento...")
        tratamento = TratamentoTabelas(arquivo=ARQUIVO_EXCEL)
        tratamento.executar_pipeline()
        tabelas = tratamento.tabelas

        print("\nCarregando tabelas no banco (respeitando dependência de FK)...\n")

        # 1. dim_materia (sem dependências)
        banco.carregar_tabela(limpar_nat(tratamento.dim_materia), "dim_materia")

        # 2. professores (depende de dim_materia)
        banco.carregar_tabela(limpar_nat(tabelas["amostra_professores"]), "professores")
        professor_ids = set(tabelas["amostra_professores"]["professor_id"])

        # 3. professor_materia (depende de professores e dim_materia).
        # A relação é montada em tratar_professores() antes do dedup por
        # nome_professor, então pode conter professor_id que não sobrevive
        # ao dedup (ex.: cadastro duplicado), filtramos aqui pelos
        # professor_id que de fato ficaram na tabela.
        professor_materia = filtrar_fk_valida(
            tratamento.professor_materia, "professor_id", professor_ids, "professor_materia"
        )
        banco.carregar_tabela(limpar_nat(professor_materia), "professor_materia")

        # 4. estudantes (sem dependências), inclui stubs para aluno_id que
        # aparecem nos fatos mas não na amostra de estudantes, senão suas
        # aprovações/presenças/resultados seriam descartados pela FK.
        estudantes = adicionar_estudantes_stub(
            tabelas["amostra_estudantes"],
            [
                tabelas["amostra_matriculas"],
                tabelas["amostra_aprovacoes"],
                tabelas["amostra_resultados_sim"],
                tabelas["amostra_presencas_aulas"],
            ],
        )
        banco.carregar_tabela(limpar_nat(estudantes), "estudantes")
        aluno_ids = set(estudantes["aluno_id"])

        # 5. ofertas_curso (depende de dim_materia e professores)
        ofertas = filtrar_fk_valida(
            tabelas["amostra_ofertas_curso"], "professor_id", professor_ids, "ofertas_curso"
        )
        banco.carregar_tabela(limpar_nat(ofertas), "ofertas_curso")
        oferta_ids = set(ofertas["oferta_id"])

        # 6. matriculas (depende de estudantes, ofertas_curso e dim_materia)
        matriculas = filtrar_fk_valida(
            tabelas["amostra_matriculas"], "aluno_id", aluno_ids, "matriculas"
        )
        matriculas = filtrar_fk_valida(matriculas, "oferta_id", oferta_ids, "matriculas")
        banco.carregar_tabela(limpar_nat(matriculas), "matriculas")

        # 7. aprovacoes (depende de estudantes)
        aprovacoes = filtrar_fk_valida(
            tabelas["amostra_aprovacoes"], "aluno_id", aluno_ids, "aprovacoes"
        )
        banco.carregar_tabela(limpar_nat(aprovacoes), "aprovacoes")

        # 8. simulados (depende de dim_materia e professores)
        simulados = filtrar_fk_valida(
            tabelas["amostra_simulados"], "professor_id", professor_ids, "simulados"
        )
        banco.carregar_tabela(limpar_nat(simulados), "simulados")
        simulado_ids = set(simulados["simulado_id"])

        # 9. resultados_sim (depende de simulados e estudantes)
        resultados = filtrar_fk_valida(
            tabelas["amostra_resultados_sim"], "simulado_id", simulado_ids, "resultados_sim"
        )
        resultados = filtrar_fk_valida(resultados, "aluno_id", aluno_ids, "resultados_sim")
        banco.carregar_tabela(limpar_nat(resultados), "resultados_sim")

        # 10. aulas (depende de ofertas_curso, dim_materia e professores)
        aulas = filtrar_fk_valida(tabelas["amostra_aulas"], "oferta_id", oferta_ids, "aulas")
        aulas = filtrar_fk_valida(aulas, "professor_id", professor_ids, "aulas")
        banco.carregar_tabela(limpar_nat(aulas), "aulas")
        aula_ids = set(aulas["aula_id"])

        # 11. presencas_aulas (depende de aulas e estudantes)
        presencas = filtrar_fk_valida(
            tabelas["amostra_presencas_aulas"], "aula_id", aula_ids, "presencas_aulas"
        )
        presencas = filtrar_fk_valida(presencas, "aluno_id", aluno_ids, "presencas_aulas")
        banco.carregar_tabela(limpar_nat(presencas), "presencas_aulas")

        print("\nBanco 'desafio_logap' construído com sucesso.")

        print("\nExportando tabelas tratadas para CSV...")
        exportar_tratados(banco)
        print(f"Dados tratados exportados em: {DIRETORIO_TRATADOS}")
    finally:
        banco.desconectar()


if __name__ == "__main__":
    main()