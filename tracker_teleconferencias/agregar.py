"""Consolida as extracoes (extracoes/*.json) em tabelas e num relatorio do
trimestre.

Gera em resultados/:
  - painel_empresas.csv: uma linha por empresa/trimestre, com tom da gestao,
    variacao contra o trimestre anterior, guidance e % de respostas evasivas.
  - temas.csv: uma linha por empresa/trimestre/tema (formato longo, bom para
    tabela dinamica ou Power BI).
  - temas_por_setor.csv: peso e sentimento medio de cada tema por setor e
    trimestre. Peso = soma da intensidade (1-3) / numero de empresas do setor
    que divulgaram no trimestre — assim setores com mais empresas nao
    "falam mais" so por serem maiores.
  - relatorio_<PERIODO>.md: rascunho do texto do trimestre para revisao.

Uso:
  python agregar.py                   # relatorio do trimestre mais recente
  python agregar.py --periodo 2025T2
"""
import argparse
import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
EXTRACOES_DIR = BASE_DIR / "extracoes"
RESULTADOS_DIR = BASE_DIR / "resultados"

NOMES_TEMAS = {
    "demanda_e_volumes": "Demanda e volumes",
    "precos_e_margens": "Preços e margens",
    "custos_e_inflacao": "Custos e inflação",
    "credito_e_inadimplencia": "Crédito e inadimplência",
    "juros_e_endividamento": "Juros e endividamento",
    "capex_e_expansao": "Capex e expansão",
    "dividendos_e_recompra": "Dividendos e recompra",
    "fusoes_e_aquisicoes": "Fusões e aquisições",
    "regulacao_e_governo": "Regulação e governo",
    "cambio_e_exterior": "Câmbio e exterior",
    "macro_brasil": "Macro Brasil",
    "concorrencia": "Concorrência",
    "tecnologia_e_ia": "Tecnologia e IA",
    "esg_e_clima": "ESG e clima",
    "gestao_e_governanca": "Gestão e governança",
    "outros": "Outros",
}


def chave_periodo(periodo: str) -> tuple[int, int]:
    ano, tri = periodo.split("T")
    return int(ano), int(tri)


def periodo_anterior(periodo: str) -> str:
    ano, tri = chave_periodo(periodo)
    return f"{ano - 1}T4" if tri == 1 else f"{ano}T{tri - 1}"


def carregar_extracoes(extracoes_dir: Path = EXTRACOES_DIR) -> list[dict]:
    arquivos = sorted(extracoes_dir.glob("*.json"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhuma extracao em {extracoes_dir}. Rode extrair.py antes.")
    registros = [json.loads(a.read_text(encoding="utf-8")) for a in arquivos]
    for r in registros:
        r["setor"] = r.get("setor") or "Sem setor"
    return registros


def montar_painel(registros: list[dict]) -> pd.DataFrame:
    linhas = []
    for r in registros:
        ext = r["extracao"]
        perguntas = ext["perguntas_analistas"]
        direcoes = [g["direcao"] for g in ext["guidance"]]
        linhas.append(
            {
                "ticker": r["ticker"],
                "setor": r["setor"],
                "periodo": r["periodo"],
                "tom_geral": ext["tom_geral"],
                "n_temas": len(ext["temas"]),
                "guidance_eleva": direcoes.count("eleva") + direcoes.count("introduz"),
                "guidance_reduz": direcoes.count("reduz") + direcoes.count("retira"),
                "n_perguntas": len(perguntas),
                "pct_evasivas": (
                    sum(p["resposta_evasiva"] for p in perguntas) / len(perguntas) if perguntas else 0.0
                ),
                "citacoes_a_revisar": len(r.get("citacoes_nao_encontradas", [])),
                "resumo": ext["resumo"],
            }
        )
    painel = pd.DataFrame(linhas)
    painel["_ordem"] = painel["periodo"].map(chave_periodo)
    painel = painel.sort_values(["ticker", "_ordem"])
    # Variacao so contra o trimestre imediatamente anterior: se a empresa
    # pulou um trimestre na base, a comparacao fica vazia em vez de enganosa.
    anterior = painel.set_index(["ticker", "periodo"])["tom_geral"]
    painel["delta_tom"] = [
        tom - anterior.get((tk, periodo_anterior(per)), float("nan"))
        for tk, per, tom in zip(painel["ticker"], painel["periodo"], painel["tom_geral"])
    ]
    return painel.drop(columns="_ordem").reset_index(drop=True)


def montar_temas(registros: list[dict]) -> pd.DataFrame:
    linhas = [
        {
            "ticker": r["ticker"],
            "setor": r["setor"],
            "periodo": r["periodo"],
            "tema": t["tema"],
            "sentimento": t["sentimento"],
            "intensidade": t["intensidade"],
            "destaque": t["destaque"],
            "citacao": t["citacao"],
        }
        for r in registros
        for t in r["extracao"]["temas"]
    ]
    return pd.DataFrame(
        linhas,
        columns=["ticker", "setor", "periodo", "tema", "sentimento", "intensidade", "destaque", "citacao"],
    )


def montar_temas_por_setor(temas: pd.DataFrame, painel: pd.DataFrame) -> pd.DataFrame:
    n_empresas = painel.groupby(["setor", "periodo"])["ticker"].nunique().rename("n_empresas")
    temas = temas.assign(sent_x_int=temas["sentimento"] * temas["intensidade"])
    agg = temas.groupby(["setor", "periodo", "tema"]).agg(
        soma_intensidade=("intensidade", "sum"),
        soma_sent_x_int=("sent_x_int", "sum"),
        n_empresas_citando=("ticker", "nunique"),
    )
    agg = agg.join(n_empresas, on=["setor", "periodo"])
    agg["peso"] = agg["soma_intensidade"] / agg["n_empresas"]
    # Sentimento medio ponderado pela intensidade: um tema central pesa mais
    # que uma mencao lateral.
    agg["sentimento_medio"] = agg["soma_sent_x_int"] / agg["soma_intensidade"]
    return agg[["n_empresas", "n_empresas_citando", "peso", "sentimento_medio"]].reset_index()


def _fmt(x: float, casas: int = 2) -> str:
    return "–" if pd.isna(x) else f"{x:+.{casas}f}"


def gerar_relatorio(
    periodo: str, registros: list[dict], painel: pd.DataFrame, temas: pd.DataFrame, por_setor: pd.DataFrame
) -> str:
    ant = periodo_anterior(periodo)
    atual = painel[painel["periodo"] == periodo]
    linhas = [
        f"# Tracker de teleconferências — {periodo}",
        "",
        f"{len(atual)} empresas em {atual['setor'].nunique()} setores. "
        f"Comparações contra {ant}. Rascunho gerado automaticamente: revisar antes de usar.",
        "",
        "## Tom da gestão por setor",
        "",
        "| Setor | Empresas | Tom médio | Δ vs trimestre anterior |",
        "|---|---|---|---|",
    ]
    tom_setor = painel.groupby(["setor", "periodo"])["tom_geral"].mean()
    for setor, grupo in atual.groupby("setor"):
        tom = tom_setor.get((setor, periodo))
        delta = tom - tom_setor.get((setor, ant), float("nan"))
        linhas.append(f"| {setor} | {len(grupo)} | {_fmt(tom)} | {_fmt(delta)} |")

    mudancas = atual.dropna(subset=["delta_tom"])
    mudancas = mudancas[mudancas["delta_tom"] != 0].sort_values("delta_tom")
    if not mudancas.empty:
        linhas += ["", "## Maiores mudanças de tom", ""]
        for _, m in pd.concat([mudancas.head(3), mudancas.tail(3)]).drop_duplicates("ticker").iterrows():
            linhas.append(f"- **{m['ticker']}** ({m['setor']}): {_fmt(m['delta_tom'], 0)} → tom {m['tom_geral']:+d}")

    peso = por_setor.groupby(["periodo", "tema"])["peso"].mean().unstack("periodo")
    if periodo in peso.columns:
        linhas += ["", "## Temas em alta e em queda", "", "Peso médio entre setores (intensidade por empresa).", ""]
        linhas += ["| Tema | Peso | Δ vs trimestre anterior |", "|---|---|---|"]
        # Tema ausente num trimestre = peso 0 (ninguem falou dele), nao "sem dado".
        atual_peso = peso[periodo].fillna(0)
        if ant in peso.columns:
            variacao = atual_peso - peso[ant].fillna(0)
            ordem = variacao.sort_values(ascending=False).index
        else:
            variacao = pd.Series(float("nan"), index=peso.index)
            ordem = atual_peso.sort_values(ascending=False).index
        for tema in ordem:
            if atual_peso[tema] == 0 and (pd.isna(variacao[tema]) or variacao[tema] == 0):
                continue
            linhas.append(f"| {NOMES_TEMAS.get(tema, tema)} | {atual_peso[tema]:.2f} | {_fmt(variacao[tema])} |")

    registros_atual = sorted(
        (r for r in registros if r["periodo"] == periodo), key=lambda r: (r["setor"], r["ticker"])
    )
    guidance = [(r["ticker"], g) for r in registros_atual for g in r["extracao"]["guidance"] if g["direcao"] != "mantem"]
    if guidance:
        linhas += ["", "## Mudanças de guidance", ""]
        for tk, g in guidance:
            linhas.append(f"- **{tk}** {g['direcao']} *{g['metrica']}*: {g['detalhe']}")

    evasivas = [
        (r["ticker"], p) for r in registros_atual for p in r["extracao"]["perguntas_analistas"] if p["resposta_evasiva"]
    ]
    if evasivas:
        linhas += ["", "## Onde a gestão desviou", ""]
        for tk, p in evasivas:
            linhas.append(f"- **{tk}** ({NOMES_TEMAS.get(p['tema'], p['tema'])}): {p['pergunta']}")

    linhas += ["", "## Por empresa", ""]
    for r in registros_atual:
        ext = r["extracao"]
        linhas += [f"### {r['ticker']} — {r['setor']} (tom {ext['tom_geral']:+d})", "", ext["resumo"], ""]
        if r.get("citacoes_nao_encontradas"):
            linhas += [f"> ⚠️ {len(r['citacoes_nao_encontradas'])} citação(ões) não encontradas na transcrição — revisar.", ""]
    return "\n".join(linhas).rstrip() + "\n"


def main(extracoes_dir: Path = EXTRACOES_DIR, resultados_dir: Path = RESULTADOS_DIR, periodo: str | None = None) -> Path:
    registros = carregar_extracoes(extracoes_dir)
    painel = montar_painel(registros)
    temas = montar_temas(registros)
    por_setor = montar_temas_por_setor(temas, painel)

    resultados_dir.mkdir(parents=True, exist_ok=True)
    painel.to_csv(resultados_dir / "painel_empresas.csv", index=False)
    temas.to_csv(resultados_dir / "temas.csv", index=False)
    por_setor.to_csv(resultados_dir / "temas_por_setor.csv", index=False)

    periodo = periodo or max(painel["periodo"], key=chave_periodo)
    relatorio = resultados_dir / f"relatorio_{periodo}.md"
    relatorio.write_text(gerar_relatorio(periodo, registros, painel, temas, por_setor), encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--periodo", help="Trimestre do relatorio, ex. 2025T2 (padrao: o mais recente).")
    args = parser.parse_args()
    print(f"Relatorio salvo em {main(periodo=args.periodo)}")
