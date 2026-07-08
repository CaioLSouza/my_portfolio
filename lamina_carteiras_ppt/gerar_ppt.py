#!/usr/bin/env python3
"""Gera a lâmina PPT da carteira atualizando os gráficos a partir da planilha Excel.

Como funciona
-------------
Os gráficos do template PPT foram originalmente copiados do Excel e ainda
guardam, no XML interno, as referências às células de origem (ex.
'Charts Base 100'!$M$4:$M$10000). Este script:

1. Abre o template .pptx e localiza todos os gráficos;
2. Para cada gráfico, lê essas referências e busca os valores atuais
   na planilha .xlsm (valores calculados, salvos pelo Excel);
3. Substitui os dados do gráfico preservando toda a formatação
   (cores, eixos, legenda, layout) do template;
4. Salva o novo .pptx.

Uso
---
    python gerar_ppt.py --template "Carteira Top Ações - Julho 2026.pptx" \
                        --planilha "Charts Lâmina Carteiras.xlsm" \
                        --saida "Carteira Top Ações - atualizada.pptx"

Requisitos: pip install python-pptx openpyxl
"""

import argparse
import datetime as dt
import re
import sys

import openpyxl
from openpyxl.utils import range_boundaries
from pptx import Presentation
from pptx.chart.data import CategoryChartData

# Namespace do DrawingML de gráficos (chartSpace XML)
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"


def qn(tag: str) -> str:
    return f"{{{C_NS}}}{tag}"


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
    print(f"  [{label}] atualizado: {len(sers)} série(s), {n} ponto(s) "
          f"({cats[0]} a {cats[-1]})")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--template", required=True, help="PPTX de template")
    ap.add_argument("--planilha", required=True, help="XLSM/XLSX com os gráficos")
    ap.add_argument("--saida", required=True, help="PPTX de saída")
    args = ap.parse_args()

    print(f"Lendo planilha: {args.planilha}")
    # data_only=True devolve os valores calculados salvos pelo Excel
    wb = openpyxl.load_workbook(args.planilha, data_only=True, read_only=False)

    print(f"Lendo template: {args.template}")
    prs = Presentation(args.template)

    updated = 0
    for slide_idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if not shape.has_chart:
                continue
            label = f"slide {slide_idx} / {shape.name}"
            if update_chart(shape.chart, wb, label):
                updated += 1

    if updated == 0:
        print("Nenhum gráfico atualizado — verifique se o template contém "
              "gráficos vinculados à planilha.", file=sys.stderr)
        sys.exit(1)

    prs.save(args.saida)
    print(f"OK: {updated} gráfico(s) atualizado(s) -> {args.saida}")


if __name__ == "__main__":
    main()
