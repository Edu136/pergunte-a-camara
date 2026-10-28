from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.transform import COLUNAS_DESPESAS, ler_csv, transformar

AMOSTRA = Path(__file__).parent / "fixtures" / "amostra_cotas.csv"


@pytest.fixture(scope="module")
def resultado():
    return transformar(ler_csv(AMOSTRA))


def test_relatorio(resultado):
    _, _, rel = resultado
    assert rel.linhas_lidas == 7
    assert rel.duplicatas_removidas == 1
    assert rel.sem_valor_removidas == 1
    assert rel.cpfs_descartados == 1
    assert rel.despesas_de_liderancas == 1
    assert rel.linhas_finais == 5


def test_colunas_das_despesas(resultado):
    _, despesas, _ = resultado
    assert list(despesas.columns) == COLUNAS_DESPESAS


def test_cpf_de_pessoa_fisica_nao_e_armazenado(resultado):
    _, despesas, _ = resultado
    locacao = despesas[despesas["categoria"].str.startswith("LOCAÇÃO")].iloc[0]
    assert pd.isna(locacao["cnpj_fornecedor"])
    assert "cnpj_cpf" not in despesas.columns


def test_cnpj_e_normalizado_para_digitos(resultado):
    _, despesas, _ = resultado
    assert "12345678000190" in set(despesas["cnpj_fornecedor"].dropna())


def test_valores_e_datas_convertidos(resultado):
    _, despesas, _ = resultado
    passagem = despesas[despesas["id_documento"] == 900001].iloc[0]
    assert passagem["valor_liquido"] == pytest.approx(1500.50)
    assert str(passagem["data_emissao"]) == "2024-01-10"


def test_compensacao_negativa_e_mantida(resultado):
    _, despesas, _ = resultado
    assert (despesas["valor_liquido"] < 0).sum() == 1


def test_lideranca_fica_sem_deputado(resultado):
    _, despesas, _ = resultado
    lideranca = despesas[despesas["nome_parlamentar"].str.startswith("LIDERANÇA")].iloc[0]
    assert pd.isna(lideranca["deputado_id"])


def test_deputado_fica_com_dados_mais_recentes(resultado):
    deputados, _, _ = resultado
    assert len(deputados) == 2
    fulano = deputados[deputados["id"] == 1001].iloc[0]
    assert fulano["partido"] == "PARTIDOB"


def test_valor_com_virgula_decimal():
    bruto = ler_csv(AMOSTRA)
    bruto.loc[0, "vlrLiquido"] = "1.234,56"
    bruto = bruto.drop(index=1)
    _, despesas, _ = transformar(bruto)
    assert despesas.loc[0, "valor_liquido"] == pytest.approx(1234.56)


def test_coluna_ausente_gera_erro():
    with pytest.raises(ValueError, match="Colunas ausentes"):
        transformar(ler_csv(AMOSTRA).drop(columns=["vlrLiquido"]))
