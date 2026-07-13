"""
Utilitários de limpeza e padronização reutilizados pelos tratamentos
das tabelas da base pré-vestibular.

Concentra aqui tudo que se repetia célula a célula no notebook de
exploração: normalização de texto, tratamento de nulos "disfarçados"
de string, conversão de datas e números, criação de dimensões e
mapeamento categoria -> id.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


class TratamentoUtils:
    """Métodos estáticos/de classe usados pelos tratamentos de cada tabela."""

    # Padrões de texto que representam nulo mas vieram como string
    # (ex: "nan", "None", "  ", "NaT", "pd.NaT")
    REGEX_NULOS_TEXTUAIS = [
        r'^\s*$',
        r'(?i)^\s*nan\s*$',
        r'(?i)^\s*nat\s*$',
        r'(?i)^\s*none\s*$',
        r'(?i)^\s*null\s*$',
        r'(?i)^\s*pd\.nat\s*$',
        r'(?i)^\s*na\s*$',
    ]

    # Nomes de colunas / abas
    @staticmethod
    def to_snake_case(texto: str) -> str:
        """Converte um texto (nome de aba/coluna) para snake_case."""
        texto = texto.strip()
        texto = re.sub(r"[^\w\s]", " ", texto)          # remove caracteres especiais
        texto = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", texto)  # CamelCase -> snake_case
        texto = re.sub(r"[\s\-]+", "_", texto)           # espaços e hífens -> _
        texto = re.sub(r"_+", "_", texto)                 # remove __
        return texto.lower()

    # Texto
    @staticmethod
    def normalizar_texto(valor):
        """Remove acentos, espaços nas pontas e coloca em minúsculo.
        Preserva nulos (retorna o próprio valor se for NA)."""
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
        """Aplica normalizar_texto em uma lista de colunas de um DataFrame."""
        df[colunas] = df[colunas].apply(lambda col: col.map(cls.normalizar_texto))
        return df

    @staticmethod
    def limpar_pontuacao(serie: pd.Series, caracteres_regex: str) -> pd.Series:
        """Remove caracteres de pontuação (ex.: parênteses, traços) de uma
        coluna de texto, preservando nulos. `caracteres_regex` é uma classe
        de caracteres regex, ex.: r'[().\\-\\s]'."""
        return serie.where(
            serie.isna(),
            serie.astype(str).str.replace(caracteres_regex, '', regex=True),
        )

    # Nulos "disfarçados" / preenchimento
    @classmethod
    def limpar_nulos_textuais(cls, serie: pd.Series) -> pd.Series:
        """Substitui strings que representam nulo (ex: 'nan', 'None', '')
        por pd.NA, mantendo nulos reais como estão."""
        return serie.replace(cls.REGEX_NULOS_TEXTUAIS, pd.NA, regex=True)

    # Preenchimento de nulos com valor padrão
    @classmethod
    def preencher_nulos(cls, serie: pd.Series, valor_padrao: str) -> pd.Series:
        """Limpa nulos disfarçados de string e preenche com um valor padrão
        (ex: 'sem observações', 'Não informado', 'sem status')."""
        return cls.limpar_nulos_textuais(serie).fillna(valor_padrao)

    # Números e datas
    @classmethod
    def tratar_numerico(cls, serie: pd.Series, valor_padrao: float = 0) -> pd.Series:
        """Limpa nulos disfarçados, converte para numérico (coerce) e
        preenche o que não converteu com `valor_padrao`."""
        serie_limpa = cls.limpar_nulos_textuais(serie)
        return pd.to_numeric(serie_limpa, errors='coerce').fillna(valor_padrao)

    @staticmethod
    def tratar_data(serie: pd.Series, formato_saida: str | None = None, dayfirst: bool = True) -> pd.Series:
        """Converte uma coluna de datas (ou datas com horário) em formatos
        mistos para string.

        Se `formato_saida` não for informado, detecta automaticamente se a
        coluna tem componente de horário (procurando ':' nos valores
        originais) e escolhe entre '%Y-%m-%d' (só data) e
        '%Y-%m-%d %H:%M:%S' (data + hora). Passe `formato_saida`
        explicitamente para forçar um formato específico.
        """
        convertida = pd.to_datetime(serie, format='mixed', dayfirst=dayfirst, errors='coerce')

        if formato_saida is None:
            tem_horario = serie.astype(str).str.contains(':', na=False).any()
            formato_saida = '%Y-%m-%d %H:%M:%S' if tem_horario else '%Y-%m-%d'

        return convertida.dt.strftime(formato_saida)

    # Dimensões e mapeamento categoria -> id
    @staticmethod
    def criar_dimensao(
        valores,
        nome_coluna_valor: str,
        nome_coluna_id: str,
        inicio_id: int = 1,
    ) -> pd.DataFrame:
        """Cria uma tabela dimensão (id, valor) a partir dos valores únicos
        (já normalizados/padronizados) de uma coluna."""
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
        """Substitui os valores de `serie` pelo id correspondente na tabela
        dimensão informada."""
        mapa = dimensao.set_index(coluna_valor)[coluna_id]
        return serie.map(mapa)

    # Relacionamentos N:N (colunas com múltiplos valores separados por delimitador)
    @staticmethod
    def explodir_coluna(
        df: pd.DataFrame,
        colunas_manter: list[str],
        coluna_explodir: str,
        separador: str = ';',
    ) -> pd.DataFrame:
        """Quebra uma coluna com múltiplos valores separados por `separador`
        em uma linha por valor (usado para criar tabelas de relacionamento,
        ex.: professor_materia)."""
        resultado = df[colunas_manter + [coluna_explodir]].copy()
        resultado[coluna_explodir] = resultado[coluna_explodir].str.split(separador)
        return resultado.explode(coluna_explodir).reset_index(drop=True)