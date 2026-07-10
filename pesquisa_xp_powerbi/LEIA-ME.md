# Pesquisa XP — pacote de migração para Power BI

Este pacote converte sua planilha **PA Principal** para um modelo limpo e fácil de
automatizar. Comece pelo **`GUIA_PowerBI.md`** (passo a passo).

## Conteúdo
- **Dados migrados (2020→2026):** `fResponses.csv` + `dimPergunta.csv` +
  `dimAlternativa.csv` + `dimPeriodo.csv` + `dimRespondente.csv`
- **Automação mensal:** `PowerQuery_NovosForms.pq` (import da pasta do Forms)
- **Cálculos:** `Medidas_DAX.txt`
- **Revisão:** `_RevisarAlternativas.csv` (alternativas auto-preenchidas)
- **Passo a passo:** `GUIA_PowerBI.md`

## Ideia em 1 frase
Separar **dados** (fato tidy) de **curadoria** (dicionários) de **apresentação**
(visuais parametrizados) — assim o mês vira "soltar o Forms na pasta → Atualizar",
sem arrastar fórmula, sem mexer em gráfico, e perguntas/alternativas novas viram
apenas uma linha nova numa tabela.
