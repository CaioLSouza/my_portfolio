"""Sessao HTTP compartilhada para os downloads do Portal de Dados Abertos da
CVM. O portal retorna 403 Forbidden para requisicoes sem headers de
navegador e, em alguns casos, sem uma visita previa a pagina do dataset
(Referer/cookies de sessao) — por isso todo download deste projeto passa por
esta sessao em vez de `requests.get` direto.
"""
import requests

PAGINA_DATASET_INF_DIARIO = "https://dados.cvm.gov.br/dataset/fi-doc-inf_diario"
PAGINA_DATASET_CADASTRO = "https://dados.cvm.gov.br/dataset/fi-cad"

SESSAO = requests.Session()
SESSAO.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,application/zip,application/octet-stream,text/html,*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
)

_paginas_visitadas: set[str] = set()


def aquecer_sessao(pagina_referencia: str) -> None:
    """Visita a pagina humana do dataset (uma vez por processo) para obter
    cookies de sessao e poder mandar um Referer valido no download do
    arquivo em si."""
    if pagina_referencia in _paginas_visitadas:
        return
    try:
        SESSAO.get(pagina_referencia, timeout=30)
    except Exception:
        pass  # se a pagina falhar, tenta baixar o arquivo mesmo assim
    SESSAO.headers.update({"Referer": pagina_referencia})
    _paginas_visitadas.add(pagina_referencia)


def resumo_erro(exc: Exception) -> str:
    """Resumo curto da resposta HTTP (se houver) para ajudar a diagnosticar
    bloqueios do tipo WAF/anti-bot (ex.: Cloudflare, Akamai, DataDome)."""
    resposta = getattr(exc, "response", None)
    if resposta is None:
        return str(exc)
    cabecalhos_relevantes = {
        chave: valor
        for chave, valor in resposta.headers.items()
        if chave.lower() in ("server", "cf-ray", "cf-mitigated", "akamai-grn", "x-datadome", "content-type")
    }
    corpo = resposta.text[:200].replace("\n", " ") if resposta.text else ""
    return f"{exc} | headers={cabecalhos_relevantes} | corpo='{corpo}'"
