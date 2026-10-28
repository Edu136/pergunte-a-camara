"""Limpeza e transformação do CSV de cotas para as tabelas do banco.

Funções puras (sem banco nem rede), para facilitar os testes.
Regras em specs/02-ingestao.md.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

# Colunas do arquivo oficial -> colunas do banco. Conferir com o arquivo real.
MAPA_COLUNAS = {
    "ideDocumento": "id_documento",
    "ideCadastro": "deputado_id",
    "txNomeParlamentar": "nome_parlamentar",
    "sgPartido": "partido",
    "sgUF": "uf",
    "codLegislatura": "legislatura",
    "numAno": "ano",
    "numMes": "mes",
    "txtDescricao": "categoria",
    "txtDescricaoEspecificacao": "subcategoria",
    "txtFornecedor": "fornecedor",
    "txtCNPJCPF": "cnpj_cpf",
    "datEmissao": "data_emissao",
    "vlrDocumento": "valor_documento",
    "vlrGlosa": "valor_glosa",
    "vlrLiquido": "valor_liquido",
    "urlDocumento": "url_documento",
}

COLUNAS_DESPESAS = [
    "id_documento", "deputado_id", "nome_parlamentar", "partido", "uf", "ano", "mes",
    "categoria", "subcategoria", "fornecedor", "cnpj_fornecedor", "data_emissao",
    "valor_documento", "valor_glosa", "valor_liquido", "url_documento",
]

COLUNAS_DEPUTADOS = ["id", "nome", "partido", "uf", "legislatura"]


@dataclass
class Relatorio:
    linhas_lidas: int = 0
    duplicatas_removidas: int = 0
    sem_valor_removidas: int = 0
    cpfs_descartados: int = 0
    despesas_de_liderancas: int = 0
    linhas_finais: int = 0
    avisos: list[str] = field(default_factory=list)

    def resumo(self) -> str:
        return (
            f"lidas={self.linhas_lidas} duplicatas={self.duplicatas_removidas} "
            f"sem_valor={self.sem_valor_removidas} cpfs_descartados={self.cpfs_descartados} "
            f"liderancas={self.despesas_de_liderancas} finais={self.linhas_finais}"
        )


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê o CSV oficial com tudo como texto; a conversão de tipos vem depois."""
    opcoes = dict(sep=";", dtype=str, keep_default_na=False, na_values=[""])
    try:
        return pd.read_csv(caminho, encoding="utf-8-sig", **opcoes)
    except UnicodeDecodeError:
        log.warning("Arquivo não está em UTF-8; tentando latin-1")
        return pd.read_csv(caminho, encoding="latin-1", **opcoes)


def _para_numero(serie: pd.Series) -> pd.Series:
    """Converte valores monetários aceitando ponto ou vírgula como separador decimal."""
    texto = serie.astype("string").str.strip()
    tem_virgula = texto.str.contains(",", na=False)
    texto = texto.where(~tem_virgula, texto.str.replace(".", "", regex=False))
    texto = texto.str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def _so_cnpj(serie: pd.Series) -> pd.Series:
    """Mantém apenas CNPJs (14 dígitos). CPFs de pessoa física são descartados (LGPD)."""
    digitos = serie.astype("string").str.replace(r"\D", "", regex=True)
    return digitos.where(digitos.str.len() == 14)


def _texto(serie: pd.Series) -> pd.Series:
    serie = serie.astype("string").str.strip()
    return serie.where(serie != "")


def transformar(bruto: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, Relatorio]:
    """Recebe o CSV bruto e devolve (deputados, despesas, relatório)."""
    rel = Relatorio(linhas_lidas=len(bruto))

    faltando = [c for c in MAPA_COLUNAS if c not in bruto.columns]
    if faltando:
        raise ValueError(f"Colunas ausentes no arquivo: {', '.join(faltando)}")

    # Duplicatas exatas (todas as colunas iguais) já foram relatadas na fonte oficial.
    sem_duplicatas = bruto.drop_duplicates()
    rel.duplicatas_removidas = len(bruto) - len(sem_duplicatas)

    df = sem_duplicatas[list(MAPA_COLUNAS)].rename(columns=MAPA_COLUNAS)

    for coluna in ["nome_parlamentar", "partido", "uf", "categoria", "subcategoria",
                   "fornecedor", "url_documento"]:
        df[coluna] = _texto(df[coluna])

    for coluna in ["deputado_id", "id_documento", "ano", "mes", "legislatura"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")

    for coluna in ["valor_documento", "valor_glosa", "valor_liquido"]:
        df[coluna] = _para_numero(df[coluna])

    df["data_emissao"] = pd.to_datetime(
        df["data_emissao"].astype("string").str[:10], format="%Y-%m-%d", errors="coerce"
    ).dt.date

    preenchidos = df["cnpj_cpf"].notna() & (df["cnpj_cpf"].astype("string").str.strip() != "")
    df["cnpj_fornecedor"] = _so_cnpj(df["cnpj_cpf"])
    rel.cpfs_descartados = int((preenchidos & df["cnpj_fornecedor"].isna()).sum())

    obrigatorios = ["valor_liquido", "ano", "mes", "categoria", "nome_parlamentar"]
    validas = df.dropna(subset=obrigatorios)
    rel.sem_valor_removidas = len(df) - len(validas)
    df = validas

    # Valores negativos são mantidos: representam compensações de bilhetes aéreos.
    rel.despesas_de_liderancas = int(df["deputado_id"].isna().sum())

    deputados = (
        df.dropna(subset=["deputado_id"])
        .sort_values(["ano", "mes"], kind="stable")
        .drop_duplicates("deputado_id", keep="last")  # dados mais recentes de cada deputado
        [["deputado_id", "nome_parlamentar", "partido", "uf", "legislatura"]]
        .rename(columns={"deputado_id": "id", "nome_parlamentar": "nome"})
    )[COLUNAS_DEPUTADOS]

    despesas = df[COLUNAS_DESPESAS].reset_index(drop=True)
    rel.linhas_finais = len(despesas)
    return deputados, despesas, rel
