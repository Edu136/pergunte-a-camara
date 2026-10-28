"""Enriquecimento opcional: fotos dos deputados pela API de Dados Abertos da Câmara."""

import logging

import httpx

log = logging.getLogger(__name__)


def buscar_fotos(api_url: str, legislaturas: list[int], cliente: httpx.Client) -> dict[int, str]:
    """Devolve {id_do_deputado: url_da_foto} para as legislaturas informadas."""
    fotos: dict[int, str] = {}
    for legislatura in legislaturas:
        pagina = 1
        while True:
            resposta = cliente.get(
                f"{api_url}/deputados",
                params={"idLegislatura": legislatura, "itens": 100, "pagina": pagina},
                headers={"Accept": "application/json"},
            )
            resposta.raise_for_status()
            dados = resposta.json().get("dados", [])
            if not dados:
                break
            for deputado in dados:
                if deputado.get("urlFoto"):
                    fotos[int(deputado["id"])] = deputado["urlFoto"]
            pagina += 1
    log.info("Fotos encontradas: %d", len(fotos))
    return fotos
