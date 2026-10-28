"""Ingestão dos dados abertos da Câmara.

Uso:
    python -m src.ingestion                    # anos definidos em ANOS no .env
    python -m src.ingestion --anos 2025        # só um ano
    python -m src.ingestion --sem-fotos        # não consulta a API de deputados
    python -m src.ingestion --forcar-download  # baixa de novo mesmo se o arquivo existir
"""

import argparse
import logging
from pathlib import Path

import httpx
import psycopg

from src.config import settings
from src.ingestion.download import baixar_cotas
from src.ingestion.fotos import buscar_fotos
from src.ingestion.load import carregar
from src.ingestion.transform import ler_csv, transformar

PASTA_DADOS = Path("data/raw")
log = logging.getLogger("ingestao")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestão das despesas da cota parlamentar")
    parser.add_argument("--anos", type=int, nargs="+", default=settings.lista_anos)
    parser.add_argument("--sem-fotos", action="store_true")
    parser.add_argument("--forcar-download", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with httpx.Client(timeout=120, follow_redirects=True) as cliente, \
            psycopg.connect(settings.database_url) as conexao:
        for ano in args.anos:
            log.info("=== Ano %d ===", ano)
            csv = baixar_cotas(ano, settings.camara_cotas_url, PASTA_DADOS, cliente,
                               forcar=args.forcar_download)
            deputados, despesas, relatorio = transformar(ler_csv(csv))
            log.info("Relatório: %s", relatorio.resumo())

            fotos = {}
            if not args.sem_fotos:
                legislaturas = sorted(int(x) for x in deputados["legislatura"].dropna().unique())
                try:
                    fotos = buscar_fotos(settings.camara_api_url, legislaturas, cliente)
                except httpx.HTTPError as erro:
                    log.warning("Não foi possível buscar fotos (%s); seguindo sem elas.", erro)

            carregar(conexao, deputados, despesas, fotos)

    log.info("Ingestão concluída.")


if __name__ == "__main__":
    main()
