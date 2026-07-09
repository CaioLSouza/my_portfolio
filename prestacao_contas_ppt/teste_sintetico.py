#!/usr/bin/env python3
"""Teste do preenchimento da Prestação de Contas com dados sintéticos, no
mesmo formato das saídas do pipeline. Valida o mapeamento contra o template
sem precisar de acesso à rede.

Uso:
    python teste_sintetico.py "Prestação de Contas - Top Ações.pptx" saida.pptx
"""
import sys

import numpy as np
import pandas as pd

from atualizar_prestacao import atualizar_prestacao_contas


def dados_sinteticos():
    idx = pd.bdate_range('2025-02-28', '2026-06-30')
    rng = np.random.default_rng(1)
    cart = 100 * np.cumprod(1 + rng.normal(0.0006, 0.011, len(idx)))
    ibov = 100 * np.cumprod(1 + rng.normal(0.0005, 0.010, len(idx)))
    df_port = pd.DataFrame({'Carteira - TOP Ações XP': cart, 'Ibovespa': ibov}, index=idx)

    comp = [
        ('Energia', 'Petrobras', 'PETR4', 0.05), ('Energia', 'PRIO', 'PRIO3', 0.05),
        ('Materiais', 'Gerdau', 'GGBR4', 0.05), ('Materiais', 'Vale', 'VALE3', 0.05),
        ('Cons. Disc.', 'Lojas Renner', 'LREN3', 0.05),
        ('Industriais', 'Localiza', 'RENT3', 0.10), ('Industriais', 'Embraer', 'EMBJ3', 0.05),
        ('Tec. Info.', 'TOTVS', 'TOTS3', 0.05), ('Imobiliário', 'Iguatemi', 'IGTI11', 0.10),
        ('Saúde', "Rede D'Or", 'RDOR3', 0.075),
        ('Utilidade Pública', 'Sabesp', 'SBSP3', 0.05), ('Utilidade Pública', 'Orizon', 'ORVR3', 0.05),
        ('Financeiro', 'B3', 'B3SA3', 0.075), ('Financeiro', 'Itaú Unibanco', 'ITUB4', 0.10),
        ('Financeiro', 'BTG Pactual', 'BPAC11', 0.05), ('Financeiro', 'Nubank', 'ROXO34', 0.05),
    ]
    df_comp = pd.DataFrame(comp, columns=['Setor', 'Companhia', 'Ticker', 'Peso'])

    rng2 = np.random.default_rng(7)
    rows = [{'Companhia': n, 'Ticker': t, 'Setor': s, 'Peso': p,
             'Retorno no mês': (ret := rng2.normal(0.0, 0.05)), 'Contribuição': p * ret}
            for s, n, t, p in comp]
    df_dec = pd.DataFrame(rows).sort_values('Contribuição', ascending=False).reset_index(drop=True)
    total = {'Companhia': 'Carteira (total)', 'Ticker': '', 'Setor': '',
             'Peso': df_dec['Peso'].sum(), 'Retorno no mês': np.nan,
             'Contribuição': df_dec['Contribuição'].sum()}
    df_dec = pd.concat([df_dec, pd.DataFrame([total])], ignore_index=True)
    return df_port, df_comp, df_dec


if __name__ == '__main__':
    template = sys.argv[1] if len(sys.argv) > 1 else 'Prestação de Contas - Top Ações.pptx'
    saida = sys.argv[2] if len(sys.argv) > 2 else 'prestacao_saida.pptx'
    df_port, df_comp, df_dec = dados_sinteticos()
    atualizar_prestacao_contas(template, saida, df_port, df_comp, df_dec,
                               ano_ref=2026, mes_ref=6)
