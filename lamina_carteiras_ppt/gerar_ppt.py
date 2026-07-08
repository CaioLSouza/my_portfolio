#!/usr/bin/env python3
"""Gera a lâmina PPT da carteira a partir da planilha Excel de gráficos.

O script atualiza, preservando toda a formatação do template:

* **Gráficos** — os gráficos do template guardam no XML as referências às
  células de origem (ex. 'Charts Base 100'!$M$4:$M$10000); o script lê os
  valores atuais dessas células e substitui os dados de cada série.
* **Tabelas de desempenho** (slide "Desempenho") — retornos mensais,
  desempenho por ativo e indicadores (Sharpe, Volatilidade, Beta), lidos
  das abas correspondentes da planilha. A tabela de ativos cresce ou
  encolhe conforme o número de linhas na planilha.
* **Datas** — os textos "D de mês de AAAA" e o título "Mês AAAA" são
  trocados pela data passada em --data (padrão: hoje).

As tabelas editoriais (composição da carteira, rating, preço-alvo,
comentários) não vêm da planilha e continuam sendo editadas à mão.

Uso
---
    python gerar_ppt.py --template "Carteira Top Ações - Julho 2026.pptx" \
                        --planilha "Charts Lâmina Carteiras.xlsm" \
                        --saida "Carteira Top Ações - Agosto 2026.pptx" \
                        --carteira top_acoes --data 04/08/2026

Requisitos: pip install python-pptx openpyxl
"""

import argparse
import datetime as dt
import re
import sys
from copy import deepcopy

import openpyxl
from openpyxl.utils import range_boundaries
from pptx import Presentation
from pptx.chart.data import CategoryChartData

# Namespace do DrawingML de gráficos (chartSpace XML)
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"

MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun",
               "jul", "ago", "set", "out", "nov", "dez"]
MESES_EXTENSO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Abas de origem das tabelas, por carteira
CARTEIRAS = {
    "top_acoes": {
        "metricas": "Top Ações Portfolio Metrics",
        "retornos": "performance_top_ações",
        "ativos": "Desempenho ativo top ações_last",
    },
    "top_div": {
        "metricas": "Top Div Portfolio Metrics",
        "retornos": "performance_top_divs",
        "ativos": "Desempenho ativo div_last",
    },
    "top_smll": {
        "metricas": "Top SMLL Portfolio Metrics",
        "retornos": "performance_top_smll",
        "ativos": "Desempenho ativo small_last",
    },
}


def qn(tag: str) -> str:
    return f"{{{C_NS}}}{tag}"


def mes_ano(d) -> str:
    """2025-12-01 -> 'dez-25'"""
    return f"{MESES_ABREV[d.month - 1]}-{d.year % 100:02d}"


def pct(v, casas=1) -> str:
    return "" if v is None else f"{v:.{casas}%}"


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def parse_ref(ref: str):
    """Divide uma referência tipo "'Charts Base 100'!$M$4:$M$10000" em
    (nome_da_aba, range)."""
    m = re.match(r"^'((?:[^']|'')+)'!(.+)$", ref)
    if m:
        return m.group(1).replace("''", "'"), m.group(2)
    sheet, _, rng = ref.partition("!")
    return sheet, rng


def read_range(wb, ref: str):
    """Lê uma referência de coluna única da planilha e devolve a lista de
    valores (sem cortar vazios — o corte é feito depois, pela categoria)."""
    sheet_name, rng = parse_ref(ref)
    if sheet_name not in wb.sheetnames:
        raise KeyError(f"Aba '{sheet_name}' não encontrada na planilha")
    ws = wb[sheet_name]
    min_col, min_row, max_col, max_row = range_boundaries(rng.replace("$", ""))
    max_row = min(max_row, ws.max_row)
    if min_col != max_col:
        raise ValueError(f"Referência {ref} não é de coluna única")
    return [ws.cell(row=r, column=min_col).value for r in range(min_row, max_row + 1)]


def read_cell(wb, ref: str):
    sheet_name, rng = parse_ref(ref)
    if sheet_name not in wb.sheetnames:
        return None
    return wb[sheet_name][rng.replace("$", "").split(":")[0]].value


def series_info(ser_el):
    """Extrai de um <c:ser> as referências de categoria/valores e o nome."""
    def f_ref(parent_tag, ref_tag):
        parent = ser_el.find(qn(parent_tag))
        if parent is None:
            return None
        el = parent.find(f"{qn(ref_tag)}/{qn('f')}")
        return el.text if el is not None else None

    cat_ref = f_ref("cat", "numRef") or f_ref("cat", "strRef")
    val_ref = f_ref("val", "numRef")
    name_ref = f_ref("tx", "strRef")
    # nome do gráfico: texto literal (<c:tx><c:v>) ou cache da referência
    cached = ser_el.find(f"{qn('tx')}/{qn('v')}")
    if cached is None:
        cached = ser_el.find(f"{qn('tx')}/{qn('strRef')}/{qn('strCache')}/{qn('pt')}/{qn('v')}")
    cached_name = cached.text if cached is not None else None
    return cat_ref, val_ref, name_ref, cached_name


def update_chart(chart, wb, label: str) -> bool:
    """Reconstrói os dados de um gráfico a partir da planilha. Devolve True
    se o gráfico foi atualizado."""
    sers = chart._chartSpace.findall(f".//{qn('ser')}")
    if not sers:
        print(f"  [{label}] sem séries — ignorado")
        return False

    cat_ref, _, _, _ = series_info(sers[0])
    if cat_ref is None:
        print(f"  [{label}] sem referência de categorias — ignorado")
        return False

    raw_cats = read_range(wb, cat_ref)
    # Os ranges do template vão até a linha 10000; corta no fim real dos dados
    n = len(raw_cats)
    while n > 0 and raw_cats[n - 1] is None:
        n -= 1
    cats = raw_cats[:n]
    if not cats:
        print(f"  [{label}] categorias vazias em {cat_ref} — ignorado")
        return False
    if isinstance(cats[0], dt.datetime):
        cats = [c.date() if isinstance(c, dt.datetime) else c for c in cats]

    cat_fmt = "dd/mm/yyyy" if isinstance(cats[0], dt.date) else "General"
    data = CategoryChartData(number_format=cat_fmt)
    data.categories = cats

    for ser_el in sers:
        _, val_ref, name_ref, cached_name = series_info(ser_el)
        if val_ref is None:
            print(f"  [{label}] série sem referência de valores — ignorada")
            continue
        values = read_range(wb, val_ref)[:n]
        values += [None] * (n - len(values))
        name = (read_cell(wb, name_ref) if name_ref else None) or cached_name or ""
        data.add_series(str(name), values, number_format="General")

    chart.replace_data(data)
    print(f"  [{label}] gráfico atualizado: {len(sers)} série(s), {n} ponto(s) "
          f"({cats[0]} a {cats[-1]})")
    return True


# ---------------------------------------------------------------------------
# Texto (células de tabela e parágrafos) preservando formatação
# ---------------------------------------------------------------------------

def set_paragraph_text(para, text: str):
    """Escreve o texto no primeiro run do parágrafo (herda a formatação
    dele) e remove os runs excedentes."""
    runs = para.runs
    if not runs:
        para.text = text
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def set_cell_text(cell, text: str):
    tf = cell.text_frame
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    set_paragraph_text(tf.paragraphs[0], text)


def set_table_data_rows(table, n: int):
    """Ajusta a tabela para ter n linhas de dados (além do cabeçalho),
    clonando a última linha ou removendo as excedentes."""
    tbl = table._tbl
    trs = tbl.tr_lst
    while len(trs) - 1 < n:
        tbl.append(deepcopy(trs[-1]))
        trs = tbl.tr_lst
    while len(trs) - 1 > n:
        tbl.remove(trs[-1])
        trs = tbl.tr_lst


# ---------------------------------------------------------------------------
# Tabelas de desempenho
# ---------------------------------------------------------------------------

def sheet_rows(wb, name):
    if name not in wb.sheetnames:
        raise KeyError(f"Aba '{name}' não encontrada na planilha")
    return [list(r) for r in wb[name].iter_rows(values_only=True)]


def update_tabela_metricas(table, wb, sheet, label):
    """Indicadores (Sharpe, Volatilidade, Beta): casa cada linha da tabela
    pelo nome do indicador na 1ª coluna."""
    dados = {str(r[0]).strip(): r[1:3] for r in sheet_rows(wb, sheet)[1:] if r[0]}
    feitos = 0
    for r in range(1, len(table.rows)):
        indicador = table.cell(r, 0).text.strip()
        if indicador not in dados:
            print(f"  [{label}] indicador '{indicador}' não achado na aba — mantido")
            continue
        eh_pct = "volatilidade" in indicador.lower()
        for c, v in enumerate(dados[indicador], start=1):
            if v is not None:
                set_cell_text(table.cell(r, c), pct(v, 2) if eh_pct else f"{v:.2f}")
        feitos += 1
    print(f"  [{label}] indicadores atualizados: {feitos} linha(s)")


def update_tabela_retornos(table, wb, sheet, label):
    """Retornos mensais: colunas = Desde o início | <ano> | Últ. 12M |
    últimos N meses (mais recente primeiro). Os rótulos dos meses vêm da
    planilha, então a janela desliza sozinha a cada mês."""
    rows = sheet_rows(wb, sheet)
    header, series = rows[1], rows[2:]
    meses_cols = [i for i, v in enumerate(header) if isinstance(v, dt.datetime)]
    n_meses_ppt = len(table.columns) - 4  # 1ª col = rótulo + 3 acumulados
    meses_cols = meses_cols[:n_meses_ppt]

    # cabeçalho: ano do YTD + rótulos dos meses
    ano = header[meses_cols[0]].year if meses_cols else dt.date.today().year
    set_cell_text(table.cell(0, 2), str(ano))
    for j, col in enumerate(meses_cols, start=4):
        set_cell_text(table.cell(0, j), mes_ano(header[col]))

    # dados: linha i da tabela <- linha i da aba (rótulos da 1ª coluna do
    # template são mantidos: "Top Ações XP" / "Ibovespa")
    for i in range(1, len(table.rows)):
        if i - 1 >= len(series):
            break
        r = series[i - 1]
        set_cell_text(table.cell(i, 1), pct(r[1]))   # desde o início
        set_cell_text(table.cell(i, 2), pct(r[2]))   # YTD
        set_cell_text(table.cell(i, 3), pct(r[3]))   # últimos 12M
        for j, col in enumerate(meses_cols, start=4):
            set_cell_text(table.cell(i, j), pct(r[col]))
    print(f"  [{label}] retornos atualizados: {len(series)} série(s), "
          f"{len(meses_cols)} mês(es) até {mes_ano(header[meses_cols[0]])}")


def update_tabela_ativos(table, wb, sheet, label):
    """Desempenho por ativo: uma linha por papel, no número que vier da
    planilha. Colunas da aba: Companhia | Ticker | Setor | Peso | Data de
    entrada | desde a entrada | no mês | no ano."""
    ativos = [r for r in sheet_rows(wb, sheet)[1:] if r and r[0]]
    set_table_data_rows(table, len(ativos))
    for i, r in enumerate(ativos, start=1):
        set_cell_text(table.cell(i, 0), str(r[0]))
        set_cell_text(table.cell(i, 1), str(r[1]))
        set_cell_text(table.cell(i, 2), pct(r[3], 2))
        set_cell_text(table.cell(i, 3), mes_ano(r[4]) if r[4] else "")
        set_cell_text(table.cell(i, 4), pct(r[5]))
        set_cell_text(table.cell(i, 5), pct(r[6]))
        set_cell_text(table.cell(i, 6), pct(r[7]))
    print(f"  [{label}] desempenho por ativo atualizado: {len(ativos)} papel(is)")


def update_table(table, wb, abas, label) -> bool:
    """Identifica a tabela pelo cabeçalho e delega a atualização.
    Tabelas editoriais (composição, comentários) são deixadas intactas."""
    header = [table.cell(0, c).text.strip() for c in range(len(table.columns))]
    if header and header[0].startswith("Indicador"):
        update_tabela_metricas(table, wb, abas["metricas"], label)
    elif any(h.startswith("Desde o início") for h in header):
        update_tabela_retornos(table, wb, abas["retornos"], label)
    elif header[0] == "Companhia" and any(h.startswith("Data de entrada") for h in header):
        update_tabela_ativos(table, wb, abas["ativos"], label)
    else:
        print(f"  [{label}] tabela editorial — mantida como está")
        return False
    return True


# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------

RE_DATA_LONGA = re.compile(r"^\s*\d{1,2} de [a-zç]+ de \d{4}\s*$", re.I)
RE_MES_TITULO = re.compile(
    r"^\s*(" + "|".join(m.capitalize() for m in MESES_EXTENSO) + r")( de)? \d{4}\s*$")


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def update_datas(prs, data: dt.date):
    longa = f"{data.day} de {MESES_EXTENSO[data.month - 1]} de {data.year}"
    titulo = f"{MESES_EXTENSO[data.month - 1].capitalize()} {data.year}"
    trocas = 0
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                # campos de data automáticos (<a:fld type="datetime...">):
                # o PowerPoint recalcula ao abrir; atualizamos o texto em
                # cache para exports que não recalculam (PDF, prévias)
                for fld in para._p.findall(f"{{{A_NS}}}fld"):
                    if (fld.get("type", "").startswith("datetime")
                            and fld.find(f"{{{A_NS}}}t") is not None):
                        fld.find(f"{{{A_NS}}}t").text = longa
                        trocas += 1
                texto = "".join(r.text for r in para.runs)
                if RE_DATA_LONGA.match(texto):
                    set_paragraph_text(para, longa)
                    trocas += 1
                elif RE_MES_TITULO.match(texto):
                    set_paragraph_text(para, titulo)
                    trocas += 1
    print(f"  datas atualizadas para '{longa}' ({trocas} ocorrência(s))")


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--template", required=True, help="PPTX de template")
    ap.add_argument("--planilha", required=True, help="XLSM/XLSX com os gráficos")
    ap.add_argument("--saida", required=True, help="PPTX de saída")
    ap.add_argument("--carteira", choices=sorted(CARTEIRAS), default="top_acoes",
                    help="qual carteira define as abas de origem das tabelas")
    ap.add_argument("--data", default=None, metavar="DD/MM/AAAA",
                    help="data exibida nos slides (padrão: hoje)")
    args = ap.parse_args()

    data = (dt.datetime.strptime(args.data, "%d/%m/%Y").date()
            if args.data else dt.date.today())
    abas = CARTEIRAS[args.carteira]

    print(f"Lendo planilha: {args.planilha}")
    # data_only=True devolve os valores calculados salvos pelo Excel
    wb = openpyxl.load_workbook(args.planilha, data_only=True, read_only=False)

    print(f"Lendo template: {args.template}")
    prs = Presentation(args.template)

    updated = 0
    for slide_idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            label = f"slide {slide_idx} / {shape.name}"
            if shape.has_chart:
                updated += bool(update_chart(shape.chart, wb, label))
            elif shape.has_table:
                updated += bool(update_table(shape.table, wb, abas, label))

    update_datas(prs, data)

    if updated == 0:
        print("Nenhum gráfico ou tabela atualizado — verifique se o template "
              "corresponde à planilha.", file=sys.stderr)
        sys.exit(1)

    prs.save(args.saida)
    print(f"OK: {updated} objeto(s) atualizado(s) -> {args.saida}")


if __name__ == "__main__":
    main()
