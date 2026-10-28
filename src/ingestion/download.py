"""Download dos arquivos anuais de despesas da cota parlamentar."""

import logging
import zipfile
from pathlib import Path

import httpx

log = logging.getLogger(__name__)


def baixar_cotas(
    ano: int,
    url_modelo: str,
    pasta: Path,
    cliente: httpx.Client | None = None,
    forcar: bool = False,
) -> Path:
    """Baixa Ano-{ano}.csv.zip, extrai o CSV e devolve o caminho dele.

    Se o CSV já existir na pasta, não baixa de novo (a menos que forcar=True).
    """
    pasta.mkdir(parents=True, exist_ok=True)
    caminho_zip = pasta / f"Ano-{ano}.csv.zip"
    caminho_csv = pasta / f"Ano-{ano}.csv"

    if caminho_csv.exists() and not forcar:
        log.info("Usando arquivo já baixado: %s", caminho_csv)
        return caminho_csv

    url = url_modelo.format(ano=ano)
    log.info("Baixando %s", url)
    cliente_proprio = cliente is None
    cliente = cliente or httpx.Client(timeout=120, follow_redirects=True)
    try:
        with cliente.stream("GET", url) as resposta:
            resposta.raise_for_status()
            with caminho_zip.open("wb") as arquivo:
                for bloco in resposta.iter_bytes(chunk_size=1024 * 1024):
                    arquivo.write(bloco)
    finally:
        if cliente_proprio:
            cliente.close()

    with zipfile.ZipFile(caminho_zip) as zip_:
        nomes_csv = [n for n in zip_.namelist() if n.lower().endswith(".csv")]
        if not nomes_csv:
            raise ValueError(f"Nenhum CSV encontrado em {caminho_zip.name}")
        with zip_.open(nomes_csv[0]) as origem, caminho_csv.open("wb") as destino:
            destino.write(origem.read())

    caminho_zip.unlink()
    log.info("Arquivo pronto: %s", caminho_csv)
    return caminho_csv
