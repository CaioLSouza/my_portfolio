"""Backfill dos informes diarios dos ultimos N meses (padrao: 12), necessario
para calcular series historicas de AuM e captacao liquida por classe. Rode
uma unica vez para popular o historico inicial; o dia a dia fica a cargo do
workflow que baixa apenas o mes corrente.

Uso:
    python baixar_historico.py                # ultimos 12 meses (incl. o atual)
    python baixar_historico.py --meses 6       # ultimos 6 meses
"""
import argparse
import time
from datetime import date

from download_fundos import (
    FILTRO_PADRAO,
    baixar_informe_mensal,
    carregar_filtro_cnpjs,
    filtrar_por_cnpj,
    salvar,
)
from http_cvm import resumo_erro


def meses_anteriores(referencia: date, quantidade: int) -> list[tuple[int, int]]:
    ano, mes = referencia.year, referencia.month
    resultado = []
    for _ in range(quantidade):
        resultado.append((ano, mes))
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill de informes diarios de fundos (CVM/ANBIMA)")
    parser.add_argument("--meses", type=int, default=12, help="Quantidade de meses (incluindo o atual) a baixar")
    args = parser.parse_args()

    cnpjs = carregar_filtro_cnpjs(FILTRO_PADRAO)

    for ano, mes in meses_anteriores(date.today(), args.meses):
        try:
            df = baixar_informe_mensal(ano, mes)
        except Exception as exc:
            print(f"Aviso: falha ao baixar {ano}-{mes:02d} ({resumo_erro(exc)})")
            continue
        df = filtrar_por_cnpj(df, cnpjs)
        destino = salvar(df, ano, mes)
        print(f"{destino} ({len(df)} linhas)")
        time.sleep(1)  # evita disparar limites de requisicoes do portal


if __name__ == "__main__":
    main()
