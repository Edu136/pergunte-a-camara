import io
import zipfile

import httpx

from src.ingestion.download import baixar_cotas

CONTEUDO = b'"numAno";"vlrLiquido"\n"2025";"10.00"\n'


def _zip_em_memoria() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_:
        zip_.writestr("Ano-2025.csv", CONTEUDO)
    return buffer.getvalue()


def test_baixa_extrai_e_reaproveita(tmp_path):
    chamadas = []

    def responder(request: httpx.Request) -> httpx.Response:
        chamadas.append(str(request.url))
        return httpx.Response(200, content=_zip_em_memoria())

    cliente = httpx.Client(transport=httpx.MockTransport(responder))
    modelo = "https://exemplo.gov/cotas/Ano-{ano}.csv.zip"

    caminho = baixar_cotas(2025, modelo, tmp_path, cliente)
    assert caminho.read_bytes() == CONTEUDO
    assert chamadas == ["https://exemplo.gov/cotas/Ano-2025.csv.zip"]
    assert not (tmp_path / "Ano-2025.csv.zip").exists()

    baixar_cotas(2025, modelo, tmp_path, cliente)
    assert len(chamadas) == 1
