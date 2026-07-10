"""Coleta o numero de contas PF e a posicao (R$) da B3 e adiciona o valor no
fim das duas planilhas historicas de "Pessoa fisica na Bolsa".

Uso tipico (roda a coleta e ja grava nas planilhas, com backup):
    python atualizar_planilhas.py

Conferir antes de gravar (nao altera as planilhas):
    python atualizar_planilhas.py --dry-run

Acompanhar o navegador / diagnosticar:
    python atualizar_planilhas.py --no-headless --debug

Planilhas (colunas esperadas):
    PF na Bolsa.xlsx  ->  data | Numero    (numero de contas PF)
    Posicao PF.xlsx   ->  data | posicao   (posicao total em R$ bilhoes)
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import planilhas
import scraper_b3_pf

# Caminhos padrao das planilhas na rede da XP (podem ser trocados por --planilha-*).
BASE_REDE = (
    r"\\xpdocs\Research\Equities\Estrategia\Reports\Fluxo investidores na Bolsa"
    r"\Banco de dados\Pessoa física na Bolsa\input"
)
PLANILHA_NUMERO_PADRAO = rf"{BASE_REDE}\PF na Bolsa.xlsx"
PLANILHA_POSICAO_PADRAO = rf"{BASE_REDE}\Posição PF.xlsx"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=scraper_b3_pf.URL_FAIXA_ETARIA, help="URL da pagina da B3")
    p.add_argument("--planilha-numero", default=PLANILHA_NUMERO_PADRAO, help="xlsx do numero de contas")
    p.add_argument("--planilha-posicao", default=PLANILHA_POSICAO_PADRAO, help="xlsx da posicao")
    p.add_argument("--coluna-numero", default="Número", help="Nome da coluna de valor em PF na Bolsa.xlsx")
    p.add_argument("--coluna-posicao", default="posição", help="Nome da coluna de valor em Posição PF.xlsx")
    p.add_argument("--aba-numero", default=None, help="Aba de PF na Bolsa.xlsx (padrao: a primeira)")
    p.add_argument("--aba-posicao", default=None, help="Aba de Posição PF.xlsx (padrao: a primeira)")
    p.add_argument(
        "--fator-posicao",
        type=float,
        default=1e9,
        help="Divisor aplicado ao valor bruto (R$) para gravar em R$ bilhoes. "
        "Ajuste se a pagina exibir o valor em outra unidade (padrao: 1e9).",
    )
    p.add_argument(
        "--data",
        default="auto",
        help="Data a registrar: 'auto' (data-base lida da pagina), 'hoje', ou dd/mm/aaaa.",
    )
    p.add_argument("--dry-run", action="store_true", help="So mostra o que faria; nao grava nas planilhas")
    p.add_argument("--no-headless", dest="headless", action="store_false", help="Abre o Chrome visivel")
    p.add_argument("--sem-backup", dest="backup", action="store_false", help="Nao gera copia .bak da planilha")
    p.add_argument("--sobrescrever", action="store_true", help="Atualiza o valor se a data ja existir")
    p.add_argument("--debug", action="store_true", help="Salva o HTML renderizado em ./debug")
    p.add_argument("--timeout", type=int, default=60, help="Tempo maximo (s) esperando a tabela renderizar")
    return p.parse_args()


def resolver_data(opcao: str, data_pagina: datetime | None) -> datetime:
    if opcao == "auto":
        if data_pagina is None:
            raise SystemExit(
                "Nao foi possivel ler a data-base na pagina. Informe --data dd/mm/aaaa ou --data hoje."
            )
        return data_pagina
    if opcao == "hoje":
        return datetime.now()
    return datetime.strptime(opcao, "%d/%m/%Y")


def main() -> None:
    args = parse_args()

    dados = scraper_b3_pf.coletar(
        url=args.url,
        headless=args.headless,
        timeout=args.timeout,
        debug_dir=Path("debug") if args.debug else None,
    )

    data_registro = resolver_data(args.data, dados.data_referencia)
    posicao_bilhoes = dados.posicao_reais / args.fator_posicao

    print("=" * 64)
    print("Coleta B3 - Perfil pessoa fisica / Faixa etaria")
    print(f"  Data-base lida na pagina : {dados.data_referencia:%d/%m/%Y}" if dados.data_referencia else
          "  Data-base lida na pagina : (nao identificada)")
    print(f"  Data a registrar         : {data_registro:%d/%m/%Y}")
    print(f"  Numero de contas PF      : {dados.numero_contas:,.0f}".replace(",", "."))
    print(f"  Posicao (valor bruto R$) : {dados.posicao_reais:,.2f}")
    print(f"  Posicao (R$ bilhoes)     : {posicao_bilhoes:,.4f}   (divisor {args.fator_posicao:g})")
    print(f"  Origem dos totais        : {dados.origem_total}")
    print("=" * 64)

    resultado_numero = planilhas.anexar_valor(
        caminho=args.planilha_numero,
        valor=dados.numero_contas,
        data_referencia=data_registro,
        coluna_valor=args.coluna_numero,
        aba=args.aba_numero,
        dry_run=args.dry_run,
        fazer_backup=args.backup,
        sobrescrever=args.sobrescrever,
    )
    print(resultado_numero)

    resultado_posicao = planilhas.anexar_valor(
        caminho=args.planilha_posicao,
        valor=posicao_bilhoes,
        data_referencia=data_registro,
        coluna_valor=args.coluna_posicao,
        aba=args.aba_posicao,
        dry_run=args.dry_run,
        fazer_backup=args.backup,
        sobrescrever=args.sobrescrever,
    )
    print(resultado_posicao)


if __name__ == "__main__":
    main()
