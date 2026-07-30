"""Extração do zip da base para uma pasta de trabalho."""

from __future__ import annotations

import os
import shutil
import zipfile

# Prefixos ignorados na extração: metadados de compactação, sem conteúdo útil.
PREFIXOS_IGNORADOS = ("__MACOSX", "._", ".DS_Store")


def localizar_zip(diretorio: str) -> str:
    """Procura o arquivo .zip da base no diretório.

    Args:
        diretorio: pasta onde o zip deve estar.

    Returns:
        Caminho do arquivo .zip encontrado.

    Raises:
        FileNotFoundError: se não houver nenhum .zip no diretório.
        ValueError: se houver mais de um .zip, caso em que não há como escolher.
    """
    encontrados = sorted(
        os.path.join(diretorio, nome)
        for nome in os.listdir(diretorio)
        if nome.lower().endswith(".zip")
    )
    if not encontrados:
        raise FileNotFoundError(
            f"Nenhum arquivo .zip encontrado em {diretorio}. Coloque ali o zip da base."
        )
    if len(encontrados) > 1:
        raise ValueError(
            f"Mais de um .zip em {diretorio}: {[os.path.basename(c) for c in encontrados]}. "
            "Deixe apenas o zip da base."
        )
    return encontrados[0]


def _deve_ignorar(nome: str) -> bool:
    """Diz se uma entrada do zip é metadado de compactação."""
    partes = nome.split("/")
    return any(
        parte.startswith(PREFIXOS_IGNORADOS) or parte in PREFIXOS_IGNORADOS
        for parte in partes
        if parte
    )


def extrair(caminho_zip: str, destino: str) -> None:
    """Extrai o zip para `destino`, recriando a pasta e ignorando metadados.

    Args:
        caminho_zip: caminho do arquivo .zip.
        destino: pasta de saída. É apagada e recriada a cada execução.
    """
    shutil.rmtree(destino, ignore_errors=True)
    os.makedirs(destino, exist_ok=True)

    with zipfile.ZipFile(caminho_zip) as arquivo:
        membros = [
            nome for nome in arquivo.namelist()
            if not nome.endswith("/") and not _deve_ignorar(nome)
        ]
        arquivo.extractall(destino, members=membros)
    print(f"Zip extraído: {len(membros)} arquivos de {os.path.basename(caminho_zip)}")


def localizar_pasta_dos_dados(raiz: str, arquivos_esperados: set[str]) -> str:
    """Procura, dentro de `raiz`, a pasta que contém os CSVs da base.

    Args:
        raiz: pasta onde o zip foi extraído.
        arquivos_esperados: nomes dos arquivos que a pasta precisa ter.

    Returns:
        Caminho da pasta que contém todos os arquivos esperados.

    Raises:
        FileNotFoundError: se nenhuma pasta contiver todos eles.
    """
    for pasta_atual, _, arquivos in os.walk(raiz):
        if arquivos_esperados.issubset(set(arquivos)):
            return pasta_atual
    raise FileNotFoundError(
        f"Nenhuma pasta em {raiz} contém os arquivos esperados: "
        f"{sorted(arquivos_esperados)}"
    )


def preparar_base(diretorio_zip: str, destino: str, arquivos_esperados: set[str]) -> str:
    """Localiza o zip, extrai e devolve a pasta com os CSVs.

    Args:
        diretorio_zip: pasta onde está o zip da base.
        destino: pasta de trabalho para a extração.
        arquivos_esperados: nomes dos CSVs que a base precisa ter.

    Returns:
        Caminho da pasta pronta para leitura.
    """
    caminho_zip = localizar_zip(diretorio_zip)
    extrair(caminho_zip, destino)
    return localizar_pasta_dos_dados(destino, arquivos_esperados)
