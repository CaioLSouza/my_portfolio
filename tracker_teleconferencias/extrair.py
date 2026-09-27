"""Le as transcricoes de teleconferencias de resultados e extrai, via Claude,
um JSON estruturado por empresa/trimestre (esquema em esquema.py).

Convencao de arquivos:
  transcricoes/<TICKER>/<ANO>T<TRIMESTRE>.pdf   (ou .txt)
  ex.: transcricoes/ITUB4/2025T2.pdf

Para cada transcricao gera extracoes/<TICKER>_<PERIODO>.json. Transcricoes
que ja tem extracao sao puladas (use --forcar para reprocessar), entao o
script pode rodar a cada temporada de resultados so sobre o que e novo.

Toda citacao devolvida pelo modelo e conferida contra o texto original; as
que nao forem encontradas ficam listadas em "citacoes_nao_encontradas" no
JSON, para revisao humana antes de qualquer uso externo.

Uso:
  python extrair.py                     # processa tudo que estiver pendente
  python extrair.py --ticker ITUB4      # so uma empresa
  python extrair.py --listar            # mostra o que seria processado
"""
import argparse
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import pandas as pd

from esquema import ExtracaoTeleconferencia

BASE_DIR = Path(__file__).parent
TRANSCRICOES_DIR = BASE_DIR / "transcricoes"
EXTRACOES_DIR = BASE_DIR / "extracoes"
EMPRESAS_CSV = BASE_DIR / "empresas.csv"

MODELO = os.environ.get("TRACKER_MODELO", "claude-opus-5")
PADRAO_PERIODO = re.compile(r"^\d{4}T[1-4]$")

SYSTEM_PROMPT = """\
Voce e um analista de equity research sell-side no Brasil. Sua tarefa e ler a \
transcricao de uma teleconferencia de resultados e registrar, de forma \
estruturada, o que a gestao da empresa comunicou.

Como avaliar:
- O tom reflete a gestao (apresentacao e respostas), nao os numeros do \
trimestre em si. Uma empresa com resultado fraco mas gestao confiante sobre a \
recuperacao tem tom positivo; o contrario tambem vale.
- Seja calibrado: 0 e o tom normal de uma teleconferencia corporativa, que \
costuma ser levemente otimista. Reserve +2 e -2 para casos claros.
- Registre so os temas que de fato apareceram. Use "outros" com parcimonia.
- Guidance: registre qualquer mencao a projecoes oficiais (reafirmar conta \
como "mantem"). Nao trate opinioes vagas como guidance.
- Perguntas de analistas: uma entrada por pergunta relevante do Q&A. Marque \
como evasiva quando a gestao nao responde ao que foi perguntado.
- Citacoes devem ser copiadas literalmente da transcricao, no idioma \
original, curtas (uma ou duas frases). Nunca parafraseie dentro de uma \
citacao.
- Destaques, resumos e justificativas sempre em portugues, mesmo que a \
teleconferencia seja em ingles.
"""


def ler_transcricao(caminho: Path) -> str:
    if caminho.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n".join(pagina.extract_text() or "" for pagina in PdfReader(caminho).pages)
    return caminho.read_text(encoding="utf-8")


def carregar_empresas(caminho: Path = EMPRESAS_CSV) -> dict[str, dict]:
    if not caminho.exists():
        return {}
    df = pd.read_csv(caminho, dtype=str).fillna("")
    return {linha["ticker"]: linha for linha in df.to_dict("records")}


def listar_transcricoes(
    transcricoes_dir: Path = TRANSCRICOES_DIR, ticker: str | None = None
) -> list[tuple[str, str, Path]]:
    encontradas = []
    for arquivo in sorted(transcricoes_dir.glob("*/*")):
        if arquivo.suffix.lower() not in (".pdf", ".txt"):
            continue
        tk, periodo = arquivo.parent.name.upper(), arquivo.stem.upper()
        if not PADRAO_PERIODO.match(periodo):
            print(f"[aviso] ignorando {arquivo}: nome deve ser <ANO>T<TRIMESTRE>, ex. 2025T2")
            continue
        if ticker and tk != ticker.upper():
            continue
        encontradas.append((tk, periodo, arquivo))
    return encontradas


def caminho_extracao(ticker: str, periodo: str, extracoes_dir: Path = EXTRACOES_DIR) -> Path:
    return extracoes_dir / f"{ticker}_{periodo}.json"


def _normalizar(texto: str) -> str:
    # Compara ignorando acentos, caixa, pontuacao e quebras de linha: a
    # extracao de texto do PDF costuma quebrar linhas e hifenizar no meio das
    # frases, o que nao deve contar como citacao inventada.
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "", texto)


def citacoes_nao_encontradas(extracao: ExtracaoTeleconferencia, transcricao: str) -> list[str]:
    base = _normalizar(transcricao)
    citacoes = [t.citacao for t in extracao.temas] + [g.citacao for g in extracao.guidance]
    return [c for c in citacoes if _normalizar(c) not in base]


def extrair(
    client: anthropic.Anthropic, transcricao: str, ticker: str, periodo: str, nome_empresa: str = ""
) -> ExtracaoTeleconferencia:
    empresa = f"{ticker} ({nome_empresa})" if nome_empresa else ticker
    resposta = client.beta.messages.parse(
        model=MODELO,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        # Se o classificador de seguranca recusar (raro neste tipo de texto),
        # a API refaz o pedido num modelo alternativo em vez de devolver erro.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        # O prompt de sistema e igual para todas as teleconferencias: fica em
        # cache entre chamadas seguidas.
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Empresa: {empresa}\nPeriodo: {periodo}\n\n"
                    f"<transcricao>\n{transcricao}\n</transcricao>"
                ),
            }
        ],
        output_format=ExtracaoTeleconferencia,
    )
    if resposta.stop_reason == "refusal":
        raise RuntimeError(f"{ticker} {periodo}: pedido recusado pelo modelo ({resposta.stop_details})")
    if resposta.stop_reason == "max_tokens":
        raise RuntimeError(f"{ticker} {periodo}: resposta truncada (max_tokens)")
    return resposta.parsed_output


def processar(
    client: anthropic.Anthropic,
    ticker: str,
    periodo: str,
    arquivo: Path,
    empresas: dict[str, dict],
    extracoes_dir: Path = EXTRACOES_DIR,
) -> Path:
    transcricao = ler_transcricao(arquivo)
    if len(transcricao.strip()) < 2000:
        raise ValueError(
            f"{arquivo}: so {len(transcricao.strip())} caracteres de texto — "
            "PDF escaneado (imagem)? Converta para texto antes."
        )
    info = empresas.get(ticker, {})
    extracao = extrair(client, transcricao, ticker, periodo, info.get("nome", ""))

    destino = caminho_extracao(ticker, periodo, extracoes_dir)
    destino.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "ticker": ticker,
        "periodo": periodo,
        "setor": info.get("setor", ""),
        "arquivo_origem": arquivo.name,
        "modelo": MODELO,
        "extraido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "citacoes_nao_encontradas": citacoes_nao_encontradas(extracao, transcricao),
        "extracao": extracao.model_dump(),
    }
    destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticker", help="Processa so este ticker.")
    parser.add_argument("--forcar", action="store_true", help="Reprocessa mesmo se ja houver extracao.")
    parser.add_argument("--listar", action="store_true", help="So lista o que seria processado.")
    args = parser.parse_args()

    pendentes = [
        (tk, per, arq)
        for tk, per, arq in listar_transcricoes(ticker=args.ticker)
        if args.forcar or not caminho_extracao(tk, per).exists()
    ]
    print(f"{len(pendentes)} transcricao(oes) a processar")
    if args.listar or not pendentes:
        for tk, per, arq in pendentes:
            print(f"  {tk} {per}  <- {arq.relative_to(BASE_DIR)}")
        return

    client = anthropic.Anthropic()
    empresas = carregar_empresas()
    falhas = []
    for tk, per, arq in pendentes:
        try:
            destino = processar(client, tk, per, arq, empresas)
            nao_encontradas = json.loads(destino.read_text(encoding="utf-8"))["citacoes_nao_encontradas"]
            aviso = f"  ({len(nao_encontradas)} citacao(oes) a revisar)" if nao_encontradas else ""
            print(f"[ok] {tk} {per} -> {destino.name}{aviso}")
        except (anthropic.APIError, RuntimeError, ValueError) as erro:
            falhas.append((tk, per))
            print(f"[erro] {tk} {per}: {erro}")
    if falhas:
        raise SystemExit(f"{len(falhas)} falha(s): {falhas}")


if __name__ == "__main__":
    main()
