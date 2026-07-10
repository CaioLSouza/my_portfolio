"""Coleta o numero total de contas de pessoa fisica e a posicao total (R$)
da pagina de "Perfil de pessoas fisicas / Faixa etaria" da B3.

A pagina e um app Angular: os numeros nao vem no HTML servido, sao carregados
via chamada interna de API e renderizados no navegador. Por isso a coleta e
feita com Selenium (Chrome), abrindo a pagina, esperando a tabela renderizar e
lendo os totais direto do DOM ja montado.

A extracao e deliberadamente defensiva (procura as colunas pelo texto do
cabecalho, tolera formatacao brasileira de numeros e detecta a linha de total)
porque o layout da B3 muda de tempos em tempos. Rode com --debug para gravar o
HTML renderizado e inspecionar o que foi lido quando algo nao bater.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

URL_FAIXA_ETARIA = (
    "https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/"
    "market-data/consultas/mercado-a-vista/perfil-pessoas-fisicas/faixa-etaria/"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Palavras-chave usadas para achar as colunas certas no cabecalho da tabela.
# Sao comparadas com o cabecalho normalizado (minusculo, sem acento).
_CHAVES_QTD = ("quantidade de conta", "quantidade", "contas", "conta", "investidor", "numero")
_CHAVES_VALOR = ("valor", "posic", "custodia", "financeiro", "volume")
# Colunas de participacao percentual devem ser ignoradas na escolha das colunas.
_CHAVES_IGNORAR = ("%", "percent", "particip", "part.")


@dataclass
class DadosB3:
    """Resultado da coleta. `posicao_reais` e o valor bruto em reais lido da
    pagina (sem conversao de escala); a conversao para R$ bilhoes fica a cargo
    de quem consome (ver atualizar_planilhas.py)."""

    data_referencia: datetime | None
    numero_contas: float
    posicao_reais: float
    origem_total: str  # "linha de total" ou "soma das faixas" — para diagnostico


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _norm(valor) -> str:
    """Normaliza um rotulo de cabecalho/celula para comparacao: minusculo, sem
    acento e sem espacos duplicados."""
    return re.sub(r"\s+", " ", _sem_acento(str(valor)).strip().lower())


def _para_numero(valor) -> float | None:
    """Converte um numero no formato brasileiro (1.234.567,89 / "R$ 1,2 bi") em
    float. Retorna None quando nao ha numero utilizavel na celula."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return None if (isinstance(valor, float) and pd.isna(valor)) else float(valor)
    texto = re.sub(r"[^\d,.-]", "", str(valor))  # tira "R$", "%", espacos, etc.
    if texto in ("", "-", ".", ","):
        return None
    if "," in texto:  # virgula = separador decimal -> ponto e separador de milhar
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")  # so pontos de milhar, sem decimal
    try:
        return float(texto)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Selenium
# --------------------------------------------------------------------------- #
def criar_driver(headless: bool = True):
    """Cria o driver do Chrome. O Selenium >= 4.6 baixa/gerencia o chromedriver
    sozinho (Selenium Manager), entao basta ter o Chrome instalado."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opcoes = Options()
    # "eager" = o get() retorna no DOMContentLoaded, sem esperar o evento "load"
    # da pagina inteira. Essencial aqui: as paginas da B3 mantem rastreadores/
    # long-polling abertos, o "load" as vezes nunca dispara e o get() padrao
    # ("normal") fica travado. Os numeros ficam prontos bem antes disso.
    opcoes.page_load_strategy = "eager"
    if headless:
        opcoes.add_argument("--headless=new")
    opcoes.add_argument("--window-size=1920,1080")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument(f"--user-agent={USER_AGENT}")
    opcoes.add_argument("--lang=pt-BR")
    driver = webdriver.Chrome(options=opcoes)
    # Rede de seguranca: mesmo com "eager", limita o tempo do get() para ele nao
    # travar indefinidamente — o TimeoutException e tratado em carregar_pagina.
    driver.set_page_load_timeout(45)
    return driver


def _aceitar_cookies(driver) -> None:
    """Best-effort: fecha o banner de cookies/LGPD, que as vezes cobre a pagina.
    Ignora silenciosamente se o banner nao existir."""
    from selenium.webdriver.common.by import By

    for xpath in (
        "//button[contains(translate(., 'ACEITO', 'aceito'), 'aceit')]",
        "//button[contains(., 'OK')]",
        "//a[contains(translate(., 'ACEITO', 'aceito'), 'aceit')]",
    ):
        try:
            elementos = driver.find_elements(By.XPATH, xpath)
            if elementos:
                elementos[0].click()
                return
        except Exception:
            pass


def _tabelas_da_pagina(driver) -> list[pd.DataFrame]:
    """Le todas as tabelas HTML atualmente renderizadas na pagina."""
    try:
        return pd.read_html(driver.page_source)
    except ValueError:  # "No tables found"
        return []


def abrir_url(driver, url: str) -> None:
    """Navega ate a URL tolerando o timeout do get() — nessas paginas da B3 o
    evento "load" pode nao disparar; o conteudo ja esta la mesmo assim."""
    from selenium.common.exceptions import TimeoutException

    try:
        driver.get(url)
    except TimeoutException:
        print("Aviso: o carregamento completo estourou o tempo (normal na B3); "
              "seguindo para ler a tabela mesmo assim.")


def carregar_pagina(driver, url: str = URL_FAIXA_ETARIA, timeout: int = 60) -> None:
    """Abre a pagina e espera a tabela de dados renderizar (Angular carrega os
    numeros depois do HTML inicial)."""
    abrir_url(driver, url)
    _aceitar_cookies(driver)

    limite = time.time() + timeout
    while time.time() < limite:
        for tabela in _tabelas_da_pagina(driver):
            if _localizar_colunas(tabela) is not None:
                return
        time.sleep(1.5)
    raise TimeoutError(
        "A tabela de faixa etaria nao apareceu dentro do tempo limite. "
        "Rode com --no-headless para acompanhar, ou com --debug para salvar o HTML."
    )


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def _achar_coluna(colunas_norm: list[str], chaves: tuple[str, ...]) -> int | None:
    for indice, cabecalho in enumerate(colunas_norm):
        if any(ign in cabecalho for ign in _CHAVES_IGNORAR):
            continue
        if any(chave in cabecalho for chave in chaves):
            return indice
    return None


def _localizar_colunas(tabela: pd.DataFrame) -> tuple[int, int] | None:
    """Devolve (indice_coluna_quantidade, indice_coluna_valor) se a tabela tiver
    as duas colunas de interesse; caso contrario None."""
    if tabela.shape[1] < 2:
        return None
    colunas_norm = [_norm(c) for c in tabela.columns]
    col_qtd = _achar_coluna(colunas_norm, _CHAVES_QTD)
    col_valor = _achar_coluna(colunas_norm, _CHAVES_VALOR)
    if col_qtd is None or col_valor is None or col_qtd == col_valor:
        return None
    return col_qtd, col_valor


def extrair_dados(tabelas: list[pd.DataFrame]) -> tuple[float, float, str]:
    """A partir das tabelas da pagina, devolve (numero_contas, posicao_reais,
    origem). Usa a linha de "Total" quando existe; senao soma as faixas."""
    for tabela in tabelas:
        colunas = _localizar_colunas(tabela)
        if colunas is None:
            continue
        col_qtd, col_valor = colunas
        col_rotulo = 0 if 0 not in (col_qtd, col_valor) else None

        # 1) tenta usar uma linha explicita de "Total".
        if col_rotulo is not None:
            for _, linha in tabela.iterrows():
                if "total" in _norm(linha.iloc[col_rotulo]):
                    qtd = _para_numero(linha.iloc[col_qtd])
                    val = _para_numero(linha.iloc[col_valor])
                    if qtd is not None and val is not None:
                        return qtd, val, "linha de total"

        # 2) fallback: soma as faixas (ignorando eventual linha de total).
        def _eh_total(linha) -> bool:
            return col_rotulo is not None and "total" in _norm(linha.iloc[col_rotulo])

        faixas = tabela[~tabela.apply(_eh_total, axis=1)]
        qtds = [_para_numero(v) for v in faixas.iloc[:, col_qtd]]
        vals = [_para_numero(v) for v in faixas.iloc[:, col_valor]]
        qtds = [q for q in qtds if q is not None]
        vals = [v for v in vals if v is not None]
        if qtds and vals:
            return sum(qtds), sum(vals), "soma das faixas"

    raise ValueError(
        "Nao consegui identificar as colunas de quantidade de contas e de valor "
        "na pagina. Rode com --debug para inspecionar o HTML/tabelas lidas."
    )


def extrair_data_referencia(driver) -> datetime | None:
    """Procura no texto da pagina a data de referencia (dd/mm/aaaa ou mm/aaaa).
    Retorna a primeira encontrada, que costuma ser a data-base da consulta."""
    from selenium.webdriver.common.by import By

    texto = driver.find_element(By.TAG_NAME, "body").text
    achado = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", texto)
    if achado:
        return datetime.strptime(achado.group(0), "%d/%m/%Y")
    achado = re.search(r"\b(\d{2})/(\d{4})\b", texto)
    if achado:
        return datetime.strptime("01/" + achado.group(0), "%d/%m/%Y")
    return None


def salvar_debug(driver, debug_dir: Path) -> None:
    """Grava o HTML renderizado e um screenshot da pagina, para diagnostico
    quando a coleta falha. Nunca levanta excecao (best-effort)."""
    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "pagina_renderizada.html").write_text(driver.page_source, encoding="utf-8")
        driver.save_screenshot(str(debug_dir / "pagina.png"))
    except Exception as exc:  # pragma: no cover - diagnostico
        print(f"Aviso: falha ao salvar debug ({exc})")


def coletar(
    url: str = URL_FAIXA_ETARIA,
    headless: bool = True,
    timeout: int = 60,
    debug_dir: Path | None = None,
) -> DadosB3:
    """Fluxo completo: abre a pagina, le a tabela e devolve os totais. Se
    debug_dir for informado, salva HTML/screenshot mesmo quando algo falha."""
    driver = criar_driver(headless=headless)
    try:
        try:
            carregar_pagina(driver, url=url, timeout=timeout)
            data_ref = extrair_data_referencia(driver)
            numero, posicao, origem = extrair_dados(_tabelas_da_pagina(driver))
            return DadosB3(data_ref, numero, posicao, origem)
        finally:
            if debug_dir is not None:
                salvar_debug(driver, debug_dir)
    finally:
        driver.quit()


if __name__ == "__main__":  # execucao direta = teste rapido da coleta
    dados = coletar(headless=True)
    print(dados)
