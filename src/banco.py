"""Classe responsável pela interação com o banco Postgres do projeto."""

import io
import os
import time

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

load_dotenv()


class BancoDados:
    """Conexão e operações com o banco Postgres do projeto."""

    def __init__(self, schema_path: str | None = None):
        """Lê as credenciais do ambiente e define o caminho do schema.

        Args:
            schema_path: caminho do schema.sql. O padrão é `src/schema.sql`.
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
        """URL de conexão SQLAlchemy montada a partir das credenciais."""
        return (
            f"postgresql+psycopg2://{self.usuario}:{self.senha}"
            f"@{self.host}:{self.port}/{self.nome_banco}"
        )

    def conectar(self, tentativas: int = 15, espera_segundos: int = 2) -> Engine:
        """Cria o engine e espera o Postgres aceitar conexão.

        Args:
            tentativas: número máximo de tentativas.
            espera_segundos: espera entre tentativas.

        Returns:
            O engine SQLAlchemy conectado.

        Raises:
            RuntimeError: se não conectar depois de todas as tentativas.
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
        """Libera o engine, se houver um aberto."""
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
            print("Conexão com o Postgres encerrada.")

    def criar_db(self) -> None:
        """Aplica o schema, criando ou recriando as tabelas.

        Raises:
            RuntimeError: se `conectar()` não foi chamado antes.
        """
        if self.engine is None:
            raise RuntimeError("Chame conectar() antes de criar_db().")

        with open(self.schema_path, encoding="utf-8") as arquivo_schema:
            script = arquivo_schema.read()

        with self.engine.begin() as conexao:
            conexao.execute(text(script))
        print("Schema aplicado (tabelas criadas/recriadas).")

    def carregar_tabela(self, dataframe: pd.DataFrame, nome_tabela: str) -> None:
        """Insere um DataFrame numa tabela existente, via COPY do Postgres.

        Args:
            dataframe: dados já tratados.
            nome_tabela: tabela de destino.

        Raises:
            RuntimeError: se `conectar()` não foi chamado antes.
        """
        if self.engine is None:
            raise RuntimeError("Chame conectar() antes de carregar_tabela().")

        # CSV em memória: nulos viram campo vazio e o NULL '' do COPY os
        # reconverte para NULL no banco.
        buffer = io.StringIO()
        dataframe.to_csv(buffer, index=False, header=False, na_rep="")
        buffer.seek(0)

        colunas = ", ".join(f'"{coluna}"' for coluna in dataframe.columns)
        conexao_bruta = self.engine.raw_connection()
        try:
            with conexao_bruta.cursor() as cursor:
                cursor.copy_expert(
                    f"COPY {nome_tabela} ({colunas}) FROM STDIN WITH (FORMAT CSV, NULL '')",
                    buffer,
                )
            conexao_bruta.commit()
        finally:
            conexao_bruta.close()

        print(f"  -> {nome_tabela}: {len(dataframe)} linhas carregadas.")

    def consultar(self, query: str) -> pd.DataFrame:
        """Executa um SELECT e devolve o resultado.

        Args:
            query: instrução SQL.

        Returns:
            DataFrame com o resultado.

        Raises:
            RuntimeError: se `conectar()` não foi chamado antes.
        """
        if self.engine is None:
            raise RuntimeError("Chame conectar() antes de consultar().")
        return pd.read_sql(text(query), self.engine)