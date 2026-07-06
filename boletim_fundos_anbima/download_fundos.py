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
from datetime import date
from pathlib import Path

import pandas as pd
import requests

CVM_BASE_URL = "http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS"
DATA_DIR = Path(__file__).parent / "data"
FILTRO_PADRAO = Path(__file__).parent / "fundos_acompanhados.txt"


def baixar_informe_mensal(ano: int, mes: int) -> pd.DataFrame:
    url = f"{CVM_BASE_URL}/inf_diario_fi_{ano}{mes:02d}.csv"
    resposta = requests.get(url, timeout=60)
    resposta.raise_for_status()
    return pd.read_csv(io.BytesIO(resposta.content), sep=";", encoding="latin-1")


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
