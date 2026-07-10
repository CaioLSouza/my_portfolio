"""Diagnostico da coleta da B3: abre a pagina, espera renderizar e imprime tudo
que ajuda a entender por que o scraper nao achou os dados — titulo, quantidade
de tabelas, cabecalhos e primeiras linhas de cada tabela, datas encontradas e
trechos com palavras-chave. Salva tambem o HTML e um screenshot em ./debug.

Rode e cole a saida (e, se possivel, mande debug/pagina.png):

    python diagnostico.py            # Chrome invisivel (headless)
    python diagnostico.py --ver      # abre o Chrome na tela pra voce acompanhar
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import pandas as pd

import scraper_b3_pf as s

DEBUG_DIR = Path("debug")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostico da pagina da B3")
    parser.add_argument("--ver", dest="headless", action="store_false", help="Abre o Chrome visivel")
    parser.add_argument("--espera", type=int, default=25, help="Segundos esperando a pagina montar")
    parser.add_argument("--url", default=s.URL_FAIXA_ETARIA)
    args = parser.parse_args()

    print("Abrindo o Chrome...", flush=True)
    try:
        driver = s.criar_driver(headless=args.headless)
    except Exception as exc:
        print("\n>>> FALHOU ao iniciar o Chrome/Selenium. Provavel causa: Chrome nao")
        print(">>> instalado, ou o download do chromedriver foi bloqueado pela rede.")
        print(f">>> Erro: {type(exc).__name__}: {exc}")
        sys.exit(1)

    try:
        driver.get(args.url)
        s._aceitar_cookies(driver)
        print(f"Pagina aberta. Esperando {args.espera}s a tabela renderizar...", flush=True)

        # espera ate aparecer uma tabela com as colunas certas, ou o tempo acabar
        limite = time.time() + args.espera
        while time.time() < limite:
            if any(s._localizar_colunas(t) is not None for t in s._tabelas_da_pagina(driver)):
                break
            time.sleep(1.5)

        s.salvar_debug(driver, DEBUG_DIR)

        print("\n" + "=" * 70)
        print(f"Titulo da pagina : {driver.title}")
        print(f"URL atual        : {driver.current_url}")

        tabelas = s._tabelas_da_pagina(driver)
        print(f"Tabelas HTML encontradas: {len(tabelas)}")
        for i, tabela in enumerate(tabelas):
            print(f"\n----- Tabela #{i} | shape={tabela.shape} -----")
            print("colunas:", list(tabela.columns))
            achou = s._localizar_colunas(tabela)
            print("colunas de interesse detectadas:", achou if achou else "NENHUMA")
            with pd.option_context("display.max_columns", None, "display.width", 200):
                print(tabela.head(4).to_string())

        # datas e trechos relevantes no texto da pagina
        from selenium.webdriver.common.by import By

        texto = driver.find_element(By.TAG_NAME, "body").text
        datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b|\b\d{2}/\d{4}\b", texto)
        print("\nDatas encontradas no texto:", datas[:10])

        chaves = ("faixa", "conta", "investidor", "posic", "custodia", "valor", "total")
        linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
        relevantes = [ln for ln in linhas if any(k in s._sem_acento(ln).lower() for k in chaves)]
        print("\nLinhas com palavras-chave (ate 25):")
        for ln in relevantes[:25]:
            print("  |", ln[:120])

        print("\n" + "=" * 70)
        print(f"HTML e screenshot salvos em: {DEBUG_DIR.resolve()}")
        print("Cole essa saida no chat (e mande debug/pagina.png se puder).")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
