# Consolidação da base ANBIMA (fluxo de investidores)

Consolida o relatório mensal da ANBIMA (`Dados ambima.xlsx`) com a base
histórica própria (`Histórico.xlsx`), gerando a base consolidada
(`Base XP.xlsx`). A cada execução, os **últimos 12 meses** do relatório da
ANBIMA são aplicados sobre o histórico (*upsert*): meses já existentes têm os
valores substituídos pela vintage mais recente (capturando revisões da
ANBIMA) e meses novos são acrescentados; todo o restante do histórico é
preservado.

## Abas consolidadas

| Aba (Histórico / Base XP) | Fonte (Dados ambima.xlsx) | Observações |
|---|---|---|
| `PL Const. Por Classe` | `Pág. 3 - PL Const. por Categ.` | Renda Fixa, Ações, Multimercados, Previdência, ETF e Total (R$ mi constantes). |
| `Cap. Líq. Por Classe` | `Pág. 8 - Cap. Líq. por Classe` | Mantém o layout ano → meses (1–12); os totais anuais dos anos afetados também são atualizados (o ano corrente recebe o acumulado do ano). |
| `PL por Tipo` | `Pág. 5 - PL por Tipo` | Bloco de tipos de Ações (a página da ANBIMA é transposta: meses nas colunas). `Ações Sustentabilidade / Governança` foi descontinuado pela ANBIMA e fica vazio nos meses novos. |
| `Cap. Líq. Tipo` | `Pág. 9 - Cap. Líq. por Tipo` | Idem acima. |

## Uso

```bash
pip install openpyxl
python consolidar_base.py                 # usa os caminhos padrão da rede (\\xpdocs\...)
python consolidar_base.py --meses 12 --anbima "..." --historico "..." --saida "..."
```

Detalhes tratados automaticamente: datas fora do dia 1º (ex.: `02/01/2025`),
rótulos de mês em texto no relatório da ANBIMA (ex.: `mai-26`), chaves
`AAAAMM` da Pág. 8 e a coluna de total da Pág. 9 (ignorada).
