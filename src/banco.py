"""Classe responsável pela interação com o banco Postgres do projeto."""

import os
import time

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

load_dotenv()


class BancoDados:
    """Encapsula a conexão e as operações com o banco Postgres do projeto.

    As credenciais são lidas do ambiente (populado a partir do .env) e
    ficam disponíveis como atributos da instância, em vez de constantes
    globais no módulo.
    """

    def __init__(self, schema_path: str | None = None):
        """Lê as credenciais do .env e define o caminho do schema SQL.

        Args:
            schema_path: caminho do arquivo schema.sql a ser aplicado por
                `criar_db()`. Se não for informado, usa "schema.sql" no
                mesmo diretório deste módulo (src/schema.sql).
        """
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.nome_banco = os.getenv("POSTGRES_DB", "desafio_logap")
        self.usuario = os.getenv("POSTGRES_USER", "logap")
        self.senha = os.getenv("POSTGRES_PASSWORD", "logap123")
        self.schema_path = schema_path or os.path.join(
            os.path.dirname(__file__), "schema.sql"
        )
        self.engine: Engine | None = None

    @property
    def url_conexao(self) -> str:
        """Monta a URL de conexão SQLAlchemy a partir dos atributos da instância."""
        return (
            f"postgresql+psycopg2://{self.usuario}:{self.senha}"
            f"@{self.host}:{self.port}/{self.nome_banco}"
        )

    def conectar(self, tentativas: int = 15, espera_segundos: int = 2) -> Engine:
        """Cria o engine de conexão e aguarda o Postgres ficar disponível.

        As tentativas repetidas são úteis ao subir via docker compose, já
        que o container do banco pode ainda não aceitar conexões no
        momento exato em que este serviço inicia.

        Args:
            tentativas: número máximo de tentativas de conexão.
            espera_segundos: tempo de espera entre tentativas.

        Returns:
            O engine SQLAlchemy conectado.

        Raises:
            RuntimeError: se não for possível conectar após todas as tentativas.
        """
        self.engine = create_engine(self.url_conexao)
        for tentativa in range(1, tentativas + 1):
            try:
                with self.engine.connect() as conexao:
                    conexao.execute(text("SELECT 1"))
                print(f"Conectado ao Postgres ({self.host}:{self.port}/{self.nome_banco}).")
                return self.engine
            except OperationalError:
                print(
                    f"Postgres ainda não respondeu (tentativa {tentativa}/{tentativas}), "
                    "aguardando..."
                )
                time.sleep(espera_segundos)
        raise RuntimeError("Não foi possível conectar ao Postgres.")

    def desconectar(self) -> None:
        """Libera o engine de conexão, se houver um aberto."""
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
            print("Conexão com o Postgres encerrada.")

    def criar_db(self) -> None:
        """Aplica o schema SQL no banco, criando (ou recriando) as tabelas.

        Requer que `conectar()` já tenha sido chamado.

        Raises:
            RuntimeError: se não houver conexão ativa.
        """
        if self.engine is None:
            raise RuntimeError("Chame conectar() antes de criar_db().")

        with open(self.schema_path, encoding="utf-8") as arquivo_schema:
            script = arquivo_schema.read()

        with self.engine.begin() as conexao:
            conexao.execute(text(script))
        print("Schema aplicado (tabelas criadas/recriadas).")

    def carregar_tabela(
        self, dataframe: pd.DataFrame, nome_tabela: str, chunksize: int = 500
    ) -> None:
        """Insere um DataFrame em uma tabela já existente do banco.

        Requer que `conectar()` já tenha sido chamado.

        Args:
            dataframe: dados já tratados a inserir.
            nome_tabela: nome da tabela de destino no Postgres.
            chunksize: quantidade de linhas por lote de insert.

        Raises:
            RuntimeError: se não houver conexão ativa.
        """
        if self.engine is None:
            raise RuntimeError("Chame conectar() antes de carregar_tabela().")

        dataframe.to_sql(
            nome_tabela,
            self.engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=chunksize,
        )
        print(f"  -> {nome_tabela}: {len(dataframe)} linhas carregadas.")

    def consultar(self, query: str) -> pd.DataFrame:
        """Executa uma consulta SELECT e retorna o resultado como DataFrame.

        Requer que `conectar()` já tenha sido chamado.

        Args:
            query: instrução SQL SELECT a executar.

        Returns:
            DataFrame com o resultado da consulta.

        Raises:
            RuntimeError: se não houver conexão ativa.
        """
        if self.engine is None:
            raise RuntimeError("Chame conectar() antes de consultar().")
        return pd.read_sql(text(query), self.engine)