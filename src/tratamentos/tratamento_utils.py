"""Utilitários de limpeza reutilizados pelos tratamentos das tabelas."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


class TratamentoUtils:
    """Métodos de limpeza usados pelos tratamentos de cada tabela."""

    # Textos que representam nulo mas vieram como string.
    REGEX_NULOS_TEXTUAIS = [
        r'^\s*$',
        r'(?i)^\s*nan\s*$',
        r'(?i)^\s*nat\s*$',
        r'(?i)^\s*none\s*$',
        r'(?i)^\s*null\s*$',
        r'(?i)^\s*pd\.nat\s*$',
        r'(?i)^\s*na\s*$',
    ]

    @staticmethod
    def to_snake_case(texto: str) -> str:
        """Converte um texto para snake_case.

        Args:
            texto: nome a converter.

        Returns:
            O texto em snake_case.
        """
        texto = texto.strip()
        texto = re.sub(r"[^\w\s]", " ", texto)          # remove caracteres especiais
        texto = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", texto)  # CamelCase -> snake_case
        texto = re.sub(r"[\s\-]+", "_", texto)           # espaços e hífens -> _
        texto = re.sub(r"_+", "_", texto)                 # remove __
        return texto.lower()

    # Texto
    @staticmethod
    def normalizar_texto(valor):
        """Remove acento, espaço nas pontas e passa para minúsculo, preservando nulo.

        Args:
            valor: texto a normalizar.

        Returns:
            O texto normalizado, ou o próprio valor se for nulo.
        """
        if pd.isna(valor):
            return valor

        return (
            unicodedata.normalize('NFKD', str(valor))
            .encode('ASCII', 'ignore')
            .decode('utf-8')
            .strip()
            .lower()
        )

    @classmethod
    def normalizar_colunas(cls, df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Aplica `normalizar_texto` nas colunas informadas.

        Args:
            df: DataFrame a alterar.
            colunas: colunas a normalizar.

        Returns:
            O mesmo DataFrame, com as colunas normalizadas.
        """
        df[colunas] = df[colunas].apply(lambda col: col.map(cls.normalizar_texto))
        return df

    @staticmethod
    def limpar_pontuacao(serie: pd.Series, caracteres_regex: str) -> pd.Series:
        """Remove pontuação de uma coluna de texto, preservando nulo.

        Args:
            serie: coluna de texto.
            caracteres_regex: classe de caracteres regex, ex.: r'[()\\-\\s]'.

        Returns:
            A coluna sem os caracteres informados.
        """
        return serie.where(
            serie.isna(),
            serie.astype(str).str.replace(caracteres_regex, '', regex=True),
        )

    @classmethod
    def limpar_nulos_textuais(cls, serie: pd.Series) -> pd.Series:
        """Troca strings que representam nulo por `pd.NA`.

        Args:
            serie: coluna a limpar.

        Returns:
            A coluna com os nulos textuais convertidos.
        """
        return serie.replace(cls.REGEX_NULOS_TEXTUAIS, pd.NA, regex=True)

    @classmethod
    def preencher_nulos(cls, serie: pd.Series, valor_padrao: str) -> pd.Series:
        """Limpa nulos textuais e preenche com um valor padrão.

        Args:
            serie: coluna a preencher.
            valor_padrao: valor usado no lugar do nulo.

        Returns:
            A coluna sem nulos.
        """
        return cls.limpar_nulos_textuais(serie).fillna(valor_padrao)

    @classmethod
    def tratar_numerico(cls, serie: pd.Series, valor_padrao: float = 0) -> pd.Series:
        """Converte a coluna para numérico e preenche o que não converteu.

        Args:
            serie: coluna a converter.
            valor_padrao: valor usado onde a conversão falhar.

        Returns:
            A coluna numérica.
        """
        serie_limpa = cls.limpar_nulos_textuais(serie)
        return pd.to_numeric(serie_limpa, errors='coerce').fillna(valor_padrao)

    @staticmethod
    def tratar_data(serie: pd.Series, formato_saida: str | None = None, dayfirst: bool = True) -> pd.Series:
        """Converte uma coluna de datas em formatos mistos para string padronizada.

        Args:
            serie: coluna de datas.
            formato_saida: formato de saída. Se omitido, detecta se há horário nos
                valores e escolhe entre data e data com hora.
            dayfirst: interpreta o primeiro número como dia em datas ambíguas.

        Returns:
            A coluna como string no formato de saída.
        """
        convertida = pd.to_datetime(serie, format='mixed', dayfirst=dayfirst, errors='coerce')

        if formato_saida is None:
            tem_horario = serie.astype(str).str.contains(':', na=False).any()
            formato_saida = '%Y-%m-%d %H:%M:%S' if tem_horario else '%Y-%m-%d'

        return convertida.dt.strftime(formato_saida)

    @staticmethod
    def criar_dimensao(
        valores,
        nome_coluna_valor: str,
        nome_coluna_id: str,
        inicio_id: int = 1,
    ) -> pd.DataFrame:
        """Cria uma tabela dimensão a partir dos valores únicos de uma coluna.

        Args:
            valores: valores já normalizados.
            nome_coluna_valor: nome da coluna de valor na dimensão.
            nome_coluna_id: nome da coluna de id na dimensão.
            inicio_id: primeiro id gerado.

        Returns:
            DataFrame com as colunas de id e valor.
        """
        dim = (
            pd.DataFrame({nome_coluna_valor: sorted(pd.Series(valores).dropna().unique())})
            .reset_index(drop=True)
        )
        dim.insert(0, nome_coluna_id, range(inicio_id, inicio_id + len(dim)))
        return dim

    @staticmethod
    def mapear_para_id(
        serie: pd.Series,
        dimensao: pd.DataFrame,
        coluna_valor: str,
        coluna_id: str,
    ) -> pd.Series:
        """Troca os valores da coluna pelo id correspondente na dimensão.

        Args:
            serie: coluna com os valores a mapear.
            dimensao: DataFrame da dimensão.
            coluna_valor: coluna de valor na dimensão.
            coluna_id: coluna de id na dimensão.

        Returns:
            A coluna com os ids.
        """
        mapa = dimensao.set_index(coluna_valor)[coluna_id]
        return serie.map(mapa)

    @staticmethod
    def explodir_coluna(
        df: pd.DataFrame,
        colunas_manter: list[str],
        coluna_explodir: str,
        separador: str = ';',
    ) -> pd.DataFrame:
        """Quebra uma coluna de múltiplos valores em uma linha por valor.

        Args:
            df: DataFrame de origem.
            colunas_manter: colunas repetidas em cada linha gerada.
            coluna_explodir: coluna com os valores separados.
            separador: separador dos valores.

        Returns:
            DataFrame com uma linha por valor.
        """
        resultado = df[colunas_manter + [coluna_explodir]].copy()
        resultado[coluna_explodir] = resultado[coluna_explodir].str.split(separador)
        return resultado.explode(coluna_explodir).reset_index(drop=True)