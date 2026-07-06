"""Baixa os dados diarios de fundos de investimento (ICVM 555) publicados no
Portal de Dados Abertos da CVM, a mesma base que sustenta as estatisticas do
Boletim de Fundos de Investimento da ANBIMA (patrimonio liquido, captacao,
numero de cotistas e valor de cota por fundo).

A ANBIMA disponibiliza esses dados de forma bruta apenas via ANBIMA Feed,
uma API paga que exige credenciais OAuth2 (client_id/client_secret) obtidas
em https://developers.anbima.com.br. O Portal de Dados Abertos da CVM
(https://dados.cvm.gov.br) publica a mesma informacao regulatoria de forma
gratuita e sem necessidade de cadastro, atualizada de segunda a sabado as
08h, por isso e a fonte usada aqui.

Uso:
    python download_fundos.py                       # mes/ano corrente
    python download_fundos.py --ano 2026 --mes 6     # mes especifico
    python download_fundos.py --cnpjs 00.000.000/0001-00 11.111.111/0001-11
"""
import argparse
import io
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from http_cvm import PAGINA_DATASET_INF_DIARIO, SESSAO, aquecer_sessao

CVM_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS"
DATA_DIR = Path(__file__).parent / "data"
FILTRO_PADRAO = Path(__file__).parent / "fundos_acompanhados.txt"


def _ler_csv_de_zip(conteudo_zip: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        nome_csv = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(zf.open(nome_csv), sep=";", encoding="latin-1", low_memory=False)


def baixar_informe_mensal(ano: int, mes: int) -> pd.DataFrame:
    aquecer_sessao(PAGINA_DATASET_INF_DIARIO)
    url_base = f"{CVM_BASE_URL}/inf_diario_fi_{ano}{mes:02d}"
    try:
        # A CVM passou a publicar o informe diario compactado em .zip.
        resposta = SESSAO.get(f"{url_base}.zip", timeout=60)
        resposta.raise_for_status()
        return _ler_csv_de_zip(resposta.content)
    except requests.exceptions.HTTPError:
        # Fallback: alguns meses/portais ainda servem o .csv direto.
        resposta = SESSAO.get(f"{url_base}.csv", timeout=60)
        resposta.raise_for_status()
        return pd.read_csv(io.BytesIO(resposta.content), sep=";", encoding="latin-1", low_memory=False)


def carregar_filtro_cnpjs(caminho: Path) -> list[str]:
    if not caminho.exists():
        return []
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    return [linha.strip() for linha in linhas if linha.strip() and not linha.startswith("#")]


def filtrar_por_cnpj(df: pd.DataFrame, cnpjs: list[str]) -> pd.DataFrame:
    if not cnpjs:
        return df
    return df[df["CNPJ_FUNDO"].isin(cnpjs)]


def salvar(df: pd.DataFrame, ano: int, mes: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destino = DATA_DIR / f"informe_diario_fi_{ano}{mes:02d}.csv"
    df.to_csv(destino, index=False)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa dados diarios de fundos (base CVM/ANBIMA)")
    parser.add_argument("--ano", type=int, default=date.today().year)
    parser.add_argument("--mes", type=int, default=date.today().month)
    parser.add_argument(
        "--cnpjs",
        nargs="*",
        default=None,
        help="CNPJs para filtrar. Se omitido, usa fundos_acompanhados.txt (se existir) ou baixa todos os fundos.",
    )
    args = parser.parse_args()

    cnpjs = args.cnpjs if args.cnpjs is not None else carregar_filtro_cnpjs(FILTRO_PADRAO)

    df = baixar_informe_mensal(args.ano, args.mes)
    df = filtrar_por_cnpj(df, cnpjs)
    destino = salvar(df, args.ano, args.mes)
    print(f"Dados salvos em {destino} ({len(df)} linhas, {len(cnpjs) or 'todos os'} fundos)")


if __name__ == "__main__":
    main()
