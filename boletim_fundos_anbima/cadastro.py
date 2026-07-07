"""Constroi a tabela de classificacao ANBIMA por fundo, combinando os dois
cadastros publicados pela CVM: fundos ainda nao adaptados a Resolucao CVM 175
(cad_fi.csv, chave CNPJ_FUNDO) e fundos/classes ja adaptados
(registro_fundo_classe.zip -> registro_classe.csv, chave CNPJ_Classe).

Ambos os cadastros trazem a coluna de Classificacao ANBIMA (CLASSE_ANBIMA /
Classificacao_Anbima), usada aqui para derivar:
  - nivel1: Renda Fixa, Ações, Multimercado, Cambial ou Outros;
  - nivel2_acoes (so para nivel1 == "Ações"): Ativo, Índice, Específico ou
    Internacional (fundos com 40%+ do patrimonio no exterior).

O resultado e salvo em cadastro/classificacao_fundos.csv (pequeno, poucos MB)
para ser versionado no repositorio, evitando recommitar os arquivos brutos
da CVM (dezenas de MB) a cada atualizacao.
"""
import io
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

from http_cvm import PAGINA_DATASET_CADASTRO, SESSAO, aquecer_sessao, normalizar_cnpj, resumo_erro

CAD_FI_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
REGISTRO_CLASSE_ZIP_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"
CADASTRO_DIR = Path(__file__).parent / "cadastro"
CLASSIFICACAO_CSV = CADASTRO_DIR / "classificacao_fundos.csv"


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
        df = pd.read_csv(
            zf.open(nome),
            sep=";",
            encoding="latin-1",
            low_memory=False,
            dtype={"CNPJ_Classe": str},
        )
    coluna_classe = "Classificacao_Anbima" if "Classificacao_Anbima" in df.columns else "Classificacao"
    return pd.DataFrame(
        {
            "fund_id": df["CNPJ_Classe"].apply(normalizar_cnpj),
            "denominacao_social": df.get("Denominacao_Social"),
            "classe_anbima_raw": df[coluna_classe],
        }
    )


def construir_classificacao() -> pd.DataFrame:
    aquecer_sessao(PAGINA_DATASET_CADASTRO)
    partes = []
    for baixar in (_baixar_cad_fi, _baixar_registro_classe):
        try:
            partes.append(baixar())
        except Exception as exc:
            print(f"Aviso: falha ao baixar cadastro via {baixar.__name__} ({resumo_erro(exc)})")

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


def carregar_ou_construir(forcar_atualizacao: bool = False) -> pd.DataFrame:
    if CLASSIFICACAO_CSV.exists() and not forcar_atualizacao:
        return pd.read_csv(CLASSIFICACAO_CSV, dtype={"fund_id": str})
    CADASTRO_DIR.mkdir(parents=True, exist_ok=True)
    df = construir_classificacao()
    df.to_csv(CLASSIFICACAO_CSV, index=False)
    return df


if __name__ == "__main__":
    df = carregar_ou_construir(forcar_atualizacao=True)
    print(f"Classificação de {len(df)} fundos salva em {CLASSIFICACAO_CSV}")
    print(df["nivel1"].value_counts())
