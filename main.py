"""Ponto de entrada da carga: extrai o zip da base, trata e envia para o Postgres."""

import os

import numpy as np
import pandas as pd

from src import extracao
from src.banco import BancoDados
from src.tratamentos.tratamento_tabelas import ARQUIVOS_CSV, TratamentoTabelas

DIRETORIO_DADOS = os.path.join(os.path.dirname(__file__), "data")
DIRETORIO_EXTRAIDO = os.path.join(DIRETORIO_DADOS, "extraido")
DIRETORIO_TRATADOS = os.path.join(DIRETORIO_DADOS, "tratados")

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
    """Troca a string literal 'NaT' por nulo, que é o que o Postgres aceita em data.

    Args:
        df: DataFrame já tratado.

    Returns:
        O mesmo DataFrame com 'NaT' substituído por NaN.
    """
    return df.replace({"NaT": np.nan, "NaT NaT": np.nan})


def filtrar_fk_valida(
    df: pd.DataFrame, coluna: str, valores_validos: set, nome_tabela: str
) -> pd.DataFrame:
    """Remove linhas cuja FK não existe na tabela referenciada.

    Args:
        df: DataFrame a filtrar.
        coluna: nome da coluna de FK.
        valores_validos: chaves válidas na tabela referenciada.
        nome_tabela: nome da tabela, usado no log.

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
    """Cria cadastro mínimo para todo aluno_id citado nos fatos e ausente do cadastro.

    Evita que a FK com `estudantes` descarte linhas linkáveis. Na base atual não
    há órfão, então nada é criado.

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
        "estavam no cadastro, adicionados como stub para preservar "
        "as linhas linkáveis."
    )
    return pd.concat([estudantes, stubs], ignore_index=True)


def criar_tratamento() -> TratamentoTabelas:
    """Extrai o zip da base e devolve o tratamento com as tabelas cruas carregadas.

    Returns:
        Instância de `TratamentoTabelas` pronta para `executar_pipeline()`.

    Raises:
        FileNotFoundError: se não houver zip em `data/` ou faltar CSV na base.
        ValueError: se houver mais de um zip em `data/`.
    """
    pasta = extracao.preparar_base(
        DIRETORIO_DADOS, DIRETORIO_EXTRAIDO, set(ARQUIVOS_CSV)
    )
    print(f"Dados em {pasta}")
    return TratamentoTabelas(diretorio_csv=pasta)


def exportar_tratados(banco: BancoDados, destino: str = DIRETORIO_TRATADOS) -> None:
    """Exporta cada tabela do banco para um CSV em `destino`.

    Args:
        banco: conexão já aberta.
        destino: diretório de saída, criado se não existir.
    """
    os.makedirs(destino, exist_ok=True)
    for tabela in TABELAS_EXPORTAR:
        df = banco.consultar(f"SELECT * FROM {tabela}")
        df.to_csv(os.path.join(destino, f"{tabela}.csv"), index=False)
        print(f"  -> {tabela}.csv ({len(df)} linhas)")


def montar_tabelas_finais(
    tratamento: TratamentoTabelas,
) -> dict[str, pd.DataFrame]:
    """Aplica filtros de FK, stubs e limpeza de 'NaT' sobre um tratamento já executado.

    Args:
        tratamento: instância com `executar_pipeline()` já chamado.

    Returns:
        Dicionário {nome_tabela: DataFrame} na ordem de dependência de FK, com o
        conteúdo exato que vai para o banco.
    """
    tabelas = tratamento.tabelas
    finais: dict[str, pd.DataFrame] = {}

    # 1. dim_materia (sem dependências)
    finais["dim_materia"] = tratamento.dim_materia

    # 2. professores (depende de dim_materia)
    finais["professores"] = tabelas["professores"]
    professor_ids = set(tabelas["professores"]["professor_id"])

    # 3. professor_materia (depende de professores e dim_materia).
    # A relação é montada em tratar_professores() antes do dedup por
    # nome_professor, então pode conter professor_id que não sobrevive
    # ao dedup (ex.: cadastro duplicado), filtramos aqui pelos
    # professor_id que de fato ficaram na tabela.
    finais["professor_materia"] = filtrar_fk_valida(
        tratamento.professor_materia, "professor_id", professor_ids, "professor_materia"
    )

    # 4. estudantes (sem dependências), inclui stubs para aluno_id que
    # aparecem nos fatos mas não no cadastro de estudantes, senão suas
    # aprovações/presenças/resultados seriam descartados pela FK.
    estudantes = adicionar_estudantes_stub(
        tabelas["estudantes"],
        [
            tabelas["matriculas"],
            tabelas["aprovacoes"],
            tabelas["resultados_sim"],
            tabelas["presencas_aulas"],
        ],
    )
    finais["estudantes"] = estudantes
    aluno_ids = set(estudantes["aluno_id"])

    # 5. ofertas_curso (depende de dim_materia e professores)
    ofertas = filtrar_fk_valida(
        tabelas["ofertas_curso"], "professor_id", professor_ids, "ofertas_curso"
    )
    finais["ofertas_curso"] = ofertas
    oferta_ids = set(ofertas["oferta_id"])

    # 6. matriculas (depende de estudantes, ofertas_curso e dim_materia)
    matriculas = filtrar_fk_valida(
        tabelas["matriculas"], "aluno_id", aluno_ids, "matriculas"
    )
    finais["matriculas"] = filtrar_fk_valida(
        matriculas, "oferta_id", oferta_ids, "matriculas"
    )

    # 7. aprovacoes (depende de estudantes)
    finais["aprovacoes"] = filtrar_fk_valida(
        tabelas["aprovacoes"], "aluno_id", aluno_ids, "aprovacoes"
    )

    # 8. simulados (depende de dim_materia e professores)
    simulados = filtrar_fk_valida(
        tabelas["simulados"], "professor_id", professor_ids, "simulados"
    )
    finais["simulados"] = simulados
    simulado_ids = set(simulados["simulado_id"])

    # 9. resultados_sim (depende de simulados e estudantes)
    resultados = filtrar_fk_valida(
        tabelas["resultados_sim"], "simulado_id", simulado_ids, "resultados_sim"
    )
    finais["resultados_sim"] = filtrar_fk_valida(
        resultados, "aluno_id", aluno_ids, "resultados_sim"
    )

    # 10. aulas (depende de ofertas_curso, dim_materia e professores)
    aulas = filtrar_fk_valida(tabelas["aulas"], "oferta_id", oferta_ids, "aulas")
    aulas = filtrar_fk_valida(aulas, "professor_id", professor_ids, "aulas")
    finais["aulas"] = aulas
    aula_ids = set(aulas["aula_id"])

    # 11. presencas_aulas (depende de aulas e estudantes)
    presencas = filtrar_fk_valida(
        tabelas["presencas_aulas"], "aula_id", aula_ids, "presencas_aulas"
    )
    finais["presencas_aulas"] = filtrar_fk_valida(
        presencas, "aluno_id", aluno_ids, "presencas_aulas"
    )

    return {nome: limpar_nat(df) for nome, df in finais.items()}


def carregar_base_tratada() -> dict[str, pd.DataFrame]:
    """Roda o pipeline e devolve as tabelas finais, sem tocar no banco.

    Returns:
        Dicionário {nome_tabela: DataFrame}.
    """
    tratamento = criar_tratamento()
    tratamento.executar_pipeline()
    return montar_tabelas_finais(tratamento)


def main() -> None:
    """Extrai a base, trata, carrega no banco e exporta os CSVs tratados."""
    banco = BancoDados()
    try:
        banco.conectar()
        banco.criar_db()

        print("\nRodando pipeline de tratamento...")
        tratamento = criar_tratamento()
        tratamento.executar_pipeline()

        print("\nCarregando tabelas no banco (respeitando dependência de FK)...\n")
        for nome, df in montar_tabelas_finais(tratamento).items():
            banco.carregar_tabela(df, nome)

        print("\nBanco 'desafio_logap' construído com sucesso.")

        print("\nExportando tabelas tratadas para CSV...")
        exportar_tratados(banco)
        print(f"Dados tratados exportados em: {DIRETORIO_TRATADOS}")
    finally:
        banco.desconectar()


if __name__ == "__main__":
    main()