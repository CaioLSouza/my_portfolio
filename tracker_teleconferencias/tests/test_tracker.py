"""Testes offline (sem chamar a API): extracoes sinteticas e um cliente falso.

Rodar a partir de tracker_teleconferencias/:  python -m pytest tests
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agregar  # noqa: E402
import extrair  # noqa: E402
from esquema import ExtracaoTeleconferencia  # noqa: E402

TRANSCRICAO = (
    "Operadora: Bom dia e bem-vindos a teleconferencia de resultados. "
    "CEO: A demanda seguiu forte no trimestre e estamos elevando o guidance de "
    "crescimento da carteira para 10% a 12%. A inadimplência ficou estável. "
) * 20


def _extracao(tom: int, temas: list[tuple[str, int, int]], guidance=(), evasivas=0, perguntas=2) -> dict:
    return {
        "tom_geral": tom,
        "justificativa_tom": "x",
        "resumo": f"Resumo com tom {tom}.",
        "temas": [
            {"tema": t, "sentimento": s, "intensidade": i, "destaque": "d", "citacao": "A demanda seguiu forte"}
            for t, s, i in temas
        ],
        "guidance": [
            {"metrica": m, "direcao": d, "detalhe": "det", "citacao": "estamos elevando o guidance"}
            for m, d in guidance
        ],
        "perguntas_analistas": [
            {"tema": "demanda_e_volumes", "pergunta": f"p{k}", "resposta_evasiva": k < evasivas}
            for k in range(perguntas)
        ],
    }


def _salvar(pasta: Path, ticker: str, periodo: str, setor: str, extracao: dict) -> None:
    ExtracaoTeleconferencia.model_validate(extracao)  # garante que o fixture segue o esquema
    registro = {"ticker": ticker, "periodo": periodo, "setor": setor, "citacoes_nao_encontradas": [], "extracao": extracao}
    (pasta / f"{ticker}_{periodo}.json").write_text(json.dumps(registro), encoding="utf-8")


@pytest.fixture
def base(tmp_path: Path) -> Path:
    ext = tmp_path / "extracoes"
    ext.mkdir()
    _salvar(ext, "ITUB4", "2025T1", "Financeiro", _extracao(0, [("credito_e_inadimplencia", -1, 3)]))
    _salvar(
        ext,
        "ITUB4",
        "2025T2",
        "Financeiro",
        _extracao(2, [("credito_e_inadimplencia", 1, 3), ("demanda_e_volumes", 2, 2)], [("carteira", "eleva")]),
    )
    _salvar(ext, "BBDC4", "2025T2", "Financeiro", _extracao(-1, [("credito_e_inadimplencia", -2, 1)], evasivas=1))
    _salvar(ext, "MGLU3", "2024T4", "Varejo", _extracao(-2, [("juros_e_endividamento", -2, 3)]))
    _salvar(ext, "MGLU3", "2025T2", "Varejo", _extracao(1, [("demanda_e_volumes", 1, 2)]))
    return tmp_path


def test_periodos():
    assert agregar.periodo_anterior("2025T1") == "2024T4"
    assert agregar.periodo_anterior("2025T3") == "2025T2"
    assert sorted(["2025T1", "2024T4", "2025T3"], key=agregar.chave_periodo) == ["2024T4", "2025T1", "2025T3"]


def test_painel_delta_so_contra_trimestre_imediatamente_anterior(base: Path):
    painel = agregar.montar_painel(agregar.carregar_extracoes(base / "extracoes")).set_index(["ticker", "periodo"])
    assert painel.at[("ITUB4", "2025T2"), "delta_tom"] == 2
    # MGLU3 pulou 2025T1: sem comparacao, em vez de comparar com 2024T4
    assert pd.isna(painel.at[("MGLU3", "2025T2"), "delta_tom"])
    assert painel.at[("ITUB4", "2025T2"), "guidance_eleva"] == 1
    assert painel.at[("BBDC4", "2025T2"), "pct_evasivas"] == 0.5


def test_temas_por_setor_normaliza_pelo_numero_de_empresas(base: Path):
    registros = agregar.carregar_extracoes(base / "extracoes")
    painel = agregar.montar_painel(registros)
    por_setor = agregar.montar_temas_por_setor(agregar.montar_temas(registros), painel).set_index(
        ["setor", "periodo", "tema"]
    )
    linha = por_setor.loc[("Financeiro", "2025T2", "credito_e_inadimplencia")]
    assert linha["n_empresas"] == 2
    assert linha["peso"] == pytest.approx((3 + 1) / 2)
    # ponderado pela intensidade: (1*3 + -2*1) / 4
    assert linha["sentimento_medio"] == pytest.approx(0.25)


def test_relatorio_end_to_end(base: Path):
    relatorio = agregar.main(base / "extracoes", base / "resultados").read_text(encoding="utf-8")
    assert relatorio.startswith("# Tracker de teleconferências — 2025T2")
    assert "| Financeiro | 2 | +0.50 | +0.50 |" in relatorio
    assert "**ITUB4** eleva *carteira*" in relatorio
    assert "## Onde a gestão desviou" in relatorio
    for nome in ("painel_empresas.csv", "temas.csv", "temas_por_setor.csv"):
        assert (base / "resultados" / nome).exists()


class _ClienteFalso:
    def __init__(self, extracao: dict, stop_reason: str = "end_turn"):
        self.chamadas = []
        resposta = SimpleNamespace(
            stop_reason=stop_reason,
            stop_details=None,
            parsed_output=ExtracaoTeleconferencia.model_validate(extracao),
        )

        def parse(**kwargs):
            self.chamadas.append(kwargs)
            return resposta

        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=parse))


def test_processar_salva_json_e_confere_citacoes(tmp_path: Path):
    pasta = tmp_path / "transcricoes" / "ITUB4"
    pasta.mkdir(parents=True)
    arquivo = pasta / "2025T2.txt"
    arquivo.write_text(TRANSCRICAO, encoding="utf-8")

    extracao = _extracao(1, [("demanda_e_volumes", 2, 3)], [("carteira", "eleva")])
    extracao["temas"].append(
        {"tema": "outros", "sentimento": 0, "intensidade": 1, "destaque": "d", "citacao": "Frase que ninguém disse."}
    )
    # quebra de linha e caixa diferentes nao devem contar como citacao inventada
    extracao["guidance"][0]["citacao"] = "ESTAMOS elevando\no guidance"
    cliente = _ClienteFalso(extracao)

    [(tk, per, arq)] = extrair.listar_transcricoes(tmp_path / "transcricoes")
    destino = extrair.processar(
        cliente, tk, per, arq, {"ITUB4": {"nome": "Itaú", "setor": "Financeiro"}}, tmp_path / "extracoes"
    )

    salvo = json.loads(destino.read_text(encoding="utf-8"))
    assert (salvo["ticker"], salvo["periodo"], salvo["setor"]) == ("ITUB4", "2025T2", "Financeiro")
    assert salvo["citacoes_nao_encontradas"] == ["Frase que ninguém disse."]
    chamada = cliente.chamadas[0]
    assert chamada["output_format"] is ExtracaoTeleconferencia
    assert "ITUB4 (Itaú)" in chamada["messages"][0]["content"]


def test_extrair_falha_em_recusa():
    cliente = _ClienteFalso(_extracao(0, []), stop_reason="refusal")
    with pytest.raises(RuntimeError, match="recusado"):
        extrair.extrair(cliente, TRANSCRICAO, "ITUB4", "2025T2")


def test_transcricao_curta_demais_e_rejeitada(tmp_path: Path):
    arquivo = tmp_path / "2025T2.txt"
    arquivo.write_text("pdf escaneado", encoding="utf-8")
    with pytest.raises(ValueError, match="escaneado"):
        extrair.processar(_ClienteFalso(_extracao(0, [])), "ITUB4", "2025T2", arquivo, {}, tmp_path)


def test_listar_ignora_nomes_fora_do_padrao(tmp_path: Path, capsys):
    pasta = tmp_path / "PETR4"
    pasta.mkdir()
    (pasta / "2025T2.pdf").write_bytes(b"")
    (pasta / "call_2t25.pdf").write_bytes(b"")
    (pasta / "notas.docx").write_bytes(b"")
    assert [(tk, per) for tk, per, _ in extrair.listar_transcricoes(tmp_path)] == [("PETR4", "2025T2")]
    assert "call_2t25" in capsys.readouterr().out
