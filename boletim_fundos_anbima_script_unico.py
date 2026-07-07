"""
Boletim de Fundos de Investimento (ANBIMA/CVM) — script unico e autocontido
=============================================================================

Baixa recorrentemente os dados diarios de fundos de investimento (ICVM 555 /
RCVM 175) publicados no Portal de Dados Abertos da CVM — a mesma base que
sustenta as estatisticas do Boletim de Fundos de Investimento da ANBIMA
(patrimonio liquido, captacao/resgate, cotistas, valor de cota) — cruza com a
classificacao ANBIMA de cada fundo e gera 3 tabelas com a evolucao mensal:

  1) resultados/aum_captacao_por_classe.csv
     AuM (patrimonio de fim de mes) e captacao liquida mensal, para
     Renda Fixa, Multimercado e Acoes.

  2) resultados/alocacao_relativa_por_classe.csv
     Alocacao de cada classe acima em % do AuM total da industria (todas as
     classes, inclusive Cambial e fundos nao classificados).

  3) resultados/acoes_subclasses.csv
     Dentro de Acoes: net flows mensais e % do AuM total de Acoes, por
     subtipo — Ativo, Indice, Especifico, Internacional (fundos com 40%+ do
     patrimonio no exterior) — segundo a classificacao ANBIMA de nivel 2.

Por que a fonte e a CVM e nao a ANBIMA diretamente?
----------------------------------------------------
O boletim da ANBIMA em si e um relatorio mensal (texto + graficos), sem
download automatizavel. Os dados brutos por tras dele so estao disponiveis
via ANBIMA Feed, uma API OAuth2 paga que exige cadastro (client_id/
client_secret) em https://developers.anbima.com.br. O Portal de Dados
Abertos da CVM (https://dados.cvm.gov.br) publica a mesma informacao
regulatoria de forma gratuita e sem cadastro, atualizada de segunda a sabado
as 08h, e desde 2023 inclui a propria classificacao ANBIMA (coluna
CLASSE_ANBIMA / Classificacao_Anbima) no cadastro de fundos — e a fonte
usada aqui.

Como usar
---------
1) Instale as dependencias (uma vez):
       pip install pandas requests

2) Rode o script (baixa os ultimos MESES_HISTORICO meses na primeira vez,
   monta a classificacao dos fundos e gera as tabelas):
       python boletim_fundos_anbima_script_unico.py

   No dia a dia, para so atualizar com o mes corrente, mude
   MESES_HISTORICO para 1 antes de rodar de novo (ou rode assim sempre —
   os meses ja fechados nao mudam mais, entao baixa-los de novo so custa
   tempo, nao gera inconsistencia).

Tudo e salvo dentro da pasta BASE_DIR (por padrao "dados_fundos_anbima" no
diretorio onde voce rodar o script):
    dados_fundos_anbima/
      data/         informes diarios brutos baixados (pode apagar depois)
      cadastro/     classificacao_fundos.csv (classificacao ANBIMA por fundo)
      resultados/   as 3 tabelas finais descritas acima
"""

import io
import re
import time
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd
import requests

# ----------------------------------------------------------------------------
# Configuracao — edite aqui conforme a sua necessidade
# ----------------------------------------------------------------------------

# Quantos meses (incluindo o atual) baixar/recalcular nesta execucao.
MESES_HISTORICO = 12

# CNPJs especificos para acompanhar (formato igual ao da CVM, ex.:
# "00.017.024/0001-53"). Deixe a lista vazia para baixar TODOS os ~16 mil
# fundos regulados pela ICVM 555 (mais completo, porem mais pesado).
CNPJS_ACOMPANHADOS: list[str] = []

# Pasta onde tudo sera salvo (relativa ao diretorio de execucao).
BASE_DIR = Path("dados_fundos_anbima")

DATA_DIR = BASE_DIR / "data"
CADASTRO_DIR = BASE_DIR / "cadastro"
RESULTADOS_DIR = BASE_DIR / "resultados"
CLASSIFICACAO_CSV = CADASTRO_DIR / "classificacao_fundos.csv"

CVM_INF_DIARIO_URL = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS"
CAD_FI_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
REGISTRO_CLASSE_ZIP_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"

# Paginas humanas do portal (CKAN), usadas so para "aquecer" a sessao antes de
# baixar os arquivos — alguns portais .gov.br bloqueiam link direto sem uma
# visita previa a pagina do dataset (Referer/cookies de sessao).
PAGINA_DATASET_INF_DIARIO = "https://dados.cvm.gov.br/dataset/fi-doc-inf_diario"
PAGINA_DATASET_CADASTRO = "https://dados.cvm.gov.br/dataset/fi-cad"

CLASSES_ALVO = ["Renda Fixa", "Multimercado", "Ações"]

# Sessao HTTP compartilhada com headers de navegador — o portal da CVM
# retorna 403 Forbidden para requisicoes sem esses cabecalhos.
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


def normalizar_cnpj(valor) -> str:
    """Mantem so os digitos do CNPJ. O cadastro da CVM (cad_fi.csv/
    registro_classe) e o informe diario costumam vir em formatacoes
    diferentes para o mesmo fundo (com/sem pontuacao) — sem essa
    normalizacao, o cruzamento entre os dois falha silenciosamente e a
    maioria dos fundos cai em "Não classificado", distorcendo as tabelas."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    if texto.lower() in ("", "nan", "none"):
        return ""
    return re.sub(r"\D", "", texto)


def _resumo_erro(exc: Exception) -> str:
    """Extrai um resumo curto da resposta HTTP (se houver) para ajudar a
    diagnosticar bloqueios do tipo WAF/anti-bot (ex.: Cloudflare, Akamai)."""
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


def _aquecer_sessao(pagina_referencia: str) -> None:
    """Visita a pagina humana do dataset para obter cookies de sessao e
    poder mandar um Referer valido na requisicao do arquivo em si."""
    try:
        SESSAO.get(pagina_referencia, timeout=30)
    except Exception:
        pass  # se a pagina falhar, tenta baixar o arquivo mesmo assim
    SESSAO.headers.update({"Referer": pagina_referencia})


# ----------------------------------------------------------------------------
# 1) Download do informe diario (patrimonio, captacao/resgate, cotistas)
# ----------------------------------------------------------------------------

def _ler_csv_de_zip(conteudo_zip: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        nome_csv = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(zf.open(nome_csv), sep=";", encoding="latin-1", low_memory=False)


def baixar_informe_mensal(ano: int, mes: int) -> pd.DataFrame:
    url_base = f"{CVM_INF_DIARIO_URL}/inf_diario_fi_{ano}{mes:02d}"
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


def filtrar_por_cnpj(df: pd.DataFrame, cnpjs: list[str]) -> pd.DataFrame:
    if not cnpjs:
        return df
    coluna = "CNPJ_FUNDO_CLASSE" if "CNPJ_FUNDO_CLASSE" in df.columns else "CNPJ_FUNDO"
    cnpjs_normalizados = {normalizar_cnpj(c) for c in cnpjs}
    return df[df[coluna].apply(normalizar_cnpj).isin(cnpjs_normalizados)]


def salvar_informe(df: pd.DataFrame, ano: int, mes: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destino = DATA_DIR / f"informe_diario_fi_{ano}{mes:02d}.csv"
    df.to_csv(destino, index=False)
    return destino


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


def baixar_historico(quantidade_meses: int) -> None:
    _aquecer_sessao(PAGINA_DATASET_INF_DIARIO)
    for ano, mes in meses_anteriores(date.today(), quantidade_meses):
        try:
            df = baixar_informe_mensal(ano, mes)
        except Exception as exc:
            print(f"Aviso: falha ao baixar {ano}-{mes:02d} ({_resumo_erro(exc)})")
            continue
        df = filtrar_por_cnpj(df, CNPJS_ACOMPANHADOS)
        destino = salvar_informe(df, ano, mes)
        print(f"  {destino} ({len(df)} linhas)")
        time.sleep(1)  # evita disparar limites de requisicoes do portal


# ----------------------------------------------------------------------------
# 2) Classificacao ANBIMA por fundo (cadastro da CVM)
# ----------------------------------------------------------------------------

def _sem_acento(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def classificar_nivel1(classe_anbima: str) -> str:
    texto = _sem_acento(classe_anbima)
    if "renda fixa" in texto:
        return "Renda Fixa"
    if "acoes" in texto or "acao" in texto:
        return "Ações"
    if "multimercado" in texto:
        return "Multimercado"
    if "cambial" in texto:
        return "Cambial"
    return "Outros"


def classificar_acoes_nivel2(classe_anbima: str) -> str:
    texto = _sem_acento(classe_anbima)
    if "exterior" in texto:
        return "Internacional"
    if "indice" in texto or "indexad" in texto:
        return "Índice"
    if "especific" in texto:
        return "Específico"
    return "Ativo"


def _baixar_cad_fi() -> pd.DataFrame:
    resposta = SESSAO.get(CAD_FI_URL, timeout=180)
    resposta.raise_for_status()
    df = pd.read_csv(
        io.BytesIO(resposta.content),
        sep=";",
        encoding="latin-1",
        low_memory=False,
        dtype={"CNPJ_FUNDO": str},
    )
    coluna_classe = "CLASSE_ANBIMA" if "CLASSE_ANBIMA" in df.columns else "CLASSE"
    return pd.DataFrame(
        {
            "fund_id": df["CNPJ_FUNDO"].apply(normalizar_cnpj),
            "denominacao_social": df.get("DENOM_SOCIAL"),
            "classe_anbima_raw": df[coluna_classe],
        }
    )


def _baixar_registro_classe() -> pd.DataFrame:
    resposta = SESSAO.get(REGISTRO_CLASSE_ZIP_URL, timeout=180)
    resposta.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as zf:
        nome = next(n for n in zf.namelist() if "registro_classe" in n.lower())
        df = pd.read_csv(zf.open(nome), sep=";", encoding="latin-1", low_memory=False, dtype={"CNPJ_Classe": str})
    coluna_classe = "Classificacao_Anbima" if "Classificacao_Anbima" in df.columns else "Classificacao"
    return pd.DataFrame(
        {
            "fund_id": df["CNPJ_Classe"].apply(normalizar_cnpj),
            "denominacao_social": df.get("Denominacao_Social"),
            "classe_anbima_raw": df[coluna_classe],
        }
    )


def construir_classificacao() -> pd.DataFrame:
    _aquecer_sessao(PAGINA_DATASET_CADASTRO)
    partes = []
    for baixar in (_baixar_cad_fi, _baixar_registro_classe):
        try:
            partes.append(baixar())
        except Exception as exc:
            print(f"Aviso: falha ao baixar cadastro via {baixar.__name__} ({_resumo_erro(exc)})")

    if not partes:
        raise RuntimeError("Não foi possível baixar nenhum cadastro de fundos da CVM")

    df = pd.concat(partes, ignore_index=True)
    df = df[df["fund_id"] != ""].drop_duplicates(subset=["fund_id"], keep="last")
    df["nivel1"] = df["classe_anbima_raw"].apply(classificar_nivel1)
    df["nivel2_acoes"] = df.apply(
        lambda linha: classificar_acoes_nivel2(linha["classe_anbima_raw"]) if linha["nivel1"] == "Ações" else "",
        axis=1,
    )
    return df


def carregar_ou_construir_classificacao(forcar_atualizacao: bool = False) -> pd.DataFrame:
    if CLASSIFICACAO_CSV.exists() and not forcar_atualizacao:
        return pd.read_csv(CLASSIFICACAO_CSV, dtype={"fund_id": str})
    CADASTRO_DIR.mkdir(parents=True, exist_ok=True)
    df = construir_classificacao()
    df.to_csv(CLASSIFICACAO_CSV, index=False)
    return df


# ----------------------------------------------------------------------------
# 3) Agregacao mensal por classe (com upsert, preserva historico entre runs)
# ----------------------------------------------------------------------------

def _coluna_ou(df: pd.DataFrame, *nomes: str) -> str:
    for nome in nomes:
        if nome in df.columns:
            return nome
    raise KeyError(f"Nenhuma das colunas {nomes} encontrada no informe diário")


def carregar_informes_diarios() -> pd.DataFrame:
    arquivos = sorted(DATA_DIR.glob("informe_diario_fi_*.csv"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum informe diário encontrado em {DATA_DIR}. Rode a etapa de download antes."
        )
    partes = []
    for arquivo in arquivos:
        df = pd.read_csv(
            arquivo,
            low_memory=False,
            dtype={"CNPJ_FUNDO_CLASSE": str, "CNPJ_FUNDO": str},
        )
        col_fundo = _coluna_ou(df, "CNPJ_FUNDO_CLASSE", "CNPJ_FUNDO")
        partes.append(
            pd.DataFrame(
                {
                    "fund_id": df[col_fundo].apply(normalizar_cnpj),
                    "dt_comptc": pd.to_datetime(df["DT_COMPTC"]),
                    "vl_patrim_liq": df["VL_PATRIM_LIQ"],
                    "captc_dia": df["CAPTC_DIA"],
                    "resg_dia": df["RESG_DIA"],
                }
            )
        )
    return pd.concat(partes, ignore_index=True)


def agregar_mensal_por_fundo(informes: pd.DataFrame) -> pd.DataFrame:
    informes = informes.copy()
    informes["ano_mes"] = informes["dt_comptc"].dt.to_period("M").astype(str)
    informes["fluxo_liquido_dia"] = informes["captc_dia"] - informes["resg_dia"]

    aum_fim_mes = (
        informes.sort_values("dt_comptc")
        .groupby(["fund_id", "ano_mes"], as_index=False)
        .last()[["fund_id", "ano_mes", "vl_patrim_liq"]]
    )
    fluxo_mes = (
        informes.groupby(["fund_id", "ano_mes"], as_index=False)["fluxo_liquido_dia"]
        .sum()
        .rename(columns={"fluxo_liquido_dia": "captacao_liquida_mes"})
    )
    return aum_fim_mes.merge(fluxo_mes, on=["fund_id", "ano_mes"])


def _upsert(df_novo: pd.DataFrame, caminho: Path, chaves: list) -> None:
    if caminho.exists():
        df_antigo = pd.read_csv(caminho)
        indice_novo = df_novo.set_index(chaves).index
        df_antigo = df_antigo[~df_antigo.set_index(chaves).index.isin(indice_novo)]
        df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    df_final = df_final.sort_values(chaves)
    df_final.to_csv(caminho, index=False)


def gerar_tabelas() -> None:
    classificacao = carregar_ou_construir_classificacao()
    # Re-normaliza defensivamente: se ja existir um classificacao_fundos.csv
    # em cache de uma execucao anterior a esta correcao, garante a mesma
    # chave de join do informe diario.
    classificacao["fund_id"] = classificacao["fund_id"].apply(normalizar_cnpj)

    informes = carregar_informes_diarios()
    por_fundo_mes = agregar_mensal_por_fundo(informes)
    por_fundo_mes = por_fundo_mes.merge(
        classificacao[["fund_id", "nivel1", "nivel2_acoes"]], on="fund_id", how="left"
    )
    por_fundo_mes["nivel1"] = por_fundo_mes["nivel1"].fillna("Não classificado")

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

    # 1) AuM e captação líquida por classe (Renda Fixa, Multimercado, Ações)
    por_classe = (
        por_fundo_mes[por_fundo_mes["nivel1"].isin(CLASSES_ALVO)]
        .groupby(["ano_mes", "nivel1"], as_index=False)
        .agg(aum=("vl_patrim_liq", "sum"), captacao_liquida=("captacao_liquida_mes", "sum"))
    )
    _upsert(por_classe, RESULTADOS_DIR / "aum_captacao_por_classe.csv", ["ano_mes", "nivel1"])

    # 2) Alocação relativa ao AuM total da indústria (todas as classes do mês)
    aum_total_mes = por_fundo_mes.groupby("ano_mes", as_index=False)["vl_patrim_liq"].sum().rename(
        columns={"vl_patrim_liq": "aum_total_industria"}
    )
    alocacao = por_classe.merge(aum_total_mes, on="ano_mes")
    alocacao["percentual_do_aum_total"] = alocacao["aum"] / alocacao["aum_total_industria"]
    _upsert(alocacao, RESULTADOS_DIR / "alocacao_relativa_por_classe.csv", ["ano_mes", "nivel1"])

    # 3) Subtipos de fundos de ações (Ativo, Índice, Específico, Internacional)
    acoes = por_fundo_mes[por_fundo_mes["nivel1"] == "Ações"]
    subclasses = acoes.groupby(["ano_mes", "nivel2_acoes"], as_index=False).agg(
        aum=("vl_patrim_liq", "sum"), captacao_liquida=("captacao_liquida_mes", "sum")
    )
    aum_total_acoes_mes = subclasses.groupby("ano_mes", as_index=False)["aum"].sum().rename(
        columns={"aum": "aum_total_acoes"}
    )
    subclasses = subclasses.merge(aum_total_acoes_mes, on="ano_mes")
    subclasses["percentual_do_aum_acoes"] = subclasses["aum"] / subclasses["aum_total_acoes"]
    _upsert(subclasses, RESULTADOS_DIR / "acoes_subclasses.csv", ["ano_mes", "nivel2_acoes"])

    print(f"Tabelas atualizadas em {RESULTADOS_DIR.resolve()}")


# ----------------------------------------------------------------------------
# Execucao ponta a ponta
# ----------------------------------------------------------------------------

def main() -> None:
    print(f"1) Baixando informes diários dos últimos {MESES_HISTORICO} mês(es)...")
    baixar_historico(MESES_HISTORICO)

    print("2) Atualizando classificação ANBIMA dos fundos (cadastro da CVM)...")
    carregar_ou_construir_classificacao(forcar_atualizacao=True)

    print("3) Gerando tabelas de AuM/captação por classe...")
    try:
        gerar_tabelas()
    except FileNotFoundError as exc:
        print(f"\nNenhum informe diário foi baixado com sucesso ({exc}).")
        print("Veja os avisos de 403/erro acima — provavelmente o portal da CVM")
        print("bloqueou as requisições. Me mande esses avisos para eu ajustar o script.")
        return

    print("\nConcluído. Resultados em:")
    for arquivo in sorted(RESULTADOS_DIR.glob("*.csv")):
        print(f"  - {arquivo.resolve()}")


if __name__ == "__main__":
    main()
