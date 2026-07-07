"""Gera as series de AuM (patrimonio liquido) e captacao liquida por classe
ANBIMA, a partir dos informes diarios ja baixados em data/ (download_fundos.py
/ baixar_historico.py) cruzados com a classificacao por fundo (cadastro.py).

Produz 3 tabelas em resultados/:
  - aum_captacao_por_classe.csv: AuM de fim de mes e captacao liquida do mes,
    para Renda Fixa, Multimercado e Ações.
  - alocacao_relativa_por_classe.csv: idem, em % do AuM total da industria
    (todas as classes, inclusive Cambial/nao classificados) naquele mes.
  - acoes_subclasses.csv: dentro de Ações, captacao liquida mensal e % do AuM
    total de Ações, por subtipo (Ativo, Índice, Específico, Internacional).

So processa os meses cujo arquivo esta presente em data/ neste momento, e faz
upsert nas tabelas existentes por ano_mes: isso permite rodar o script tanto
num backfill completo (12 meses de uma vez) quanto no dia a dia (so o mes
corrente), sem perder o historico ja consolidado em execucoes anteriores.
"""
from pathlib import Path

import pandas as pd

from cadastro import carregar_ou_construir
from http_cvm import normalizar_cnpj

DATA_DIR = Path(__file__).parent / "data"
RESULTADOS_DIR = Path(__file__).parent / "resultados"

CLASSES_ALVO = ["Renda Fixa", "Multimercado", "Ações"]


def _coluna_ou(df: pd.DataFrame, *nomes: str) -> str:
    for nome in nomes:
        if nome in df.columns:
            return nome
    raise KeyError(f"Nenhuma das colunas {nomes} encontrada no informe diário")


def carregar_informes_diarios() -> pd.DataFrame:
    arquivos = sorted(DATA_DIR.glob("informe_diario_fi_*.csv"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum informe diário encontrado em {DATA_DIR}. "
            "Rode download_fundos.py ou baixar_historico.py antes."
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
                    # Normaliza para so digitos: o cadastro (cadastro.py) usa
                    # essa mesma normalizacao, mas o informe diario da CVM
                    # costuma vir pontuado (00.017.024/0001-53) — sem isso o
                    # cruzamento com a classificacao falha silenciosamente.
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
    classificacao = carregar_ou_construir()
    # Re-normaliza defensivamente: se ja existir um classificacao_fundos.csv
    # em cache gerado antes desta correcao, garante a mesma chave de join.
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

    print(f"Tabelas atualizadas em {RESULTADOS_DIR}")


if __name__ == "__main__":
    gerar_tabelas()
