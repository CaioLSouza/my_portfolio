# Boletim de Fundos de Investimento (ANBIMA/CVM)

Download recorrente e análise dos dados diários de fundos de investimento
(ICVM 555 / RCVM 175) que sustentam as estatísticas do [Boletim de Fundos de
Investimento da ANBIMA](https://www.anbima.com.br/pt_br/informar/relatorios/fundos-de-investimento/boletim-de-fundos-de-investimentos/boletim-de-fundos-de-investimentos.htm):
patrimônio líquido (AuM), captação/resgate, número de cotistas e valor de
cota, por fundo — cruzados com a classificação ANBIMA de cada fundo.

## Por que a fonte é a CVM e não a ANBIMA diretamente?

O boletim da ANBIMA em si é um relatório mensal (texto + gráficos), sem
download automatizável. Os dados brutos por trás dele só estão disponíveis
via **ANBIMA Feed**, uma API OAuth2 paga que exige cadastro
(`client_id`/`client_secret`) em https://developers.anbima.com.br.

O [Portal de Dados Abertos da CVM](https://dados.cvm.gov.br) publica a mesma
informação regulatória de forma **gratuita, sem cadastro**, atualizada de
segunda a sábado às 08h, e desde 2023 inclui a própria **classificação
ANBIMA** (coluna `CLASSE_ANBIMA` / `Classificacao_Anbima`) no cadastro de
fundos. É a fonte usada aqui.

## Scripts

| Script | O que faz |
|---|---|
| `download_fundos.py` | Baixa o informe diário do mês corrente (roda todo dia). |
| `baixar_historico.py` | Backfill dos últimos N meses (padrão 12) — rodar uma vez para popular o histórico inicial. |
| `cadastro.py` | Baixa os cadastros de fundos da CVM (adaptados e não adaptados à RCVM 175) e deriva a classificação ANBIMA por fundo: nível 1 (Renda Fixa, Ações, Multimercado, Cambial) e, para Ações, nível 2 (Ativo, Índice, Específico, Internacional). Salva em `cadastro/classificacao_fundos.csv`. |
| `analise_classes.py` | Cruza os informes diários presentes em `data/` com a classificação e gera/atualiza as tabelas em `resultados/`. |

Os informes diários brutos (`data/*.csv`) **não são versionados** (ver
`.gitignore`) — são grandes (dezenas de MB/mês) e só servem de insumo
intermediário. O que fica no repositório são a classificação de fundos
(`cadastro/`, poucos MB) e as tabelas agregadas (`resultados/`, poucos KB),
que crescem uma linha por mês, não por fundo.

## Tabelas geradas em `resultados/`

- **`aum_captacao_por_classe.csv`**: `ano_mes, nivel1, aum, captacao_liquida`
  — evolução do AuM (patrimônio de fim de mês) e da captação líquida do mês,
  para Renda Fixa, Multimercado e Ações.
- **`alocacao_relativa_por_classe.csv`**: `ano_mes, nivel1, aum,
  aum_total_industria, percentual_do_aum_total` — alocação de cada classe
  acima em relação ao AuM total da indústria (todas as classes, inclusive
  Cambial e fundos não classificados).
- **`acoes_subclasses.csv`**: `ano_mes, nivel2_acoes, aum, captacao_liquida,
  aum_total_acoes, percentual_do_aum_acoes` — dentro de Ações, captação
  líquida mensal e % do AuM total de Ações por subtipo: Ativo, Índice,
  Específico, Internacional (fundos com 40%+ do patrimônio no exterior).

`analise_classes.py` faz *upsert* por `ano_mes`: cada execução só processa
os meses cujo arquivo está presente em `data/` naquele momento e substitui
apenas as linhas correspondentes nas tabelas acima, preservando o histórico
já consolidado em execuções anteriores.

## Uso manual

```bash
pip install -r requirements.txt
python download_fundos.py                 # mes/ano corrente
python baixar_historico.py --meses 12      # backfill inicial
python cadastro.py                         # classificação ANBIMA por fundo
python analise_classes.py                  # gera/atualiza as tabelas
```

## Automação (GitHub Actions)

- **`.github/workflows/download-fundos-anbima.yml`**: roda todo dia, baixa o
  mês corrente, atualiza a classificação e as tabelas de `resultados/`, e
  faz commit automático.
- **`.github/workflows/backfill-historico-fundos.yml`**: manual
  (`workflow_dispatch`), para popular ou estender o histórico inicial (input
  `meses`, padrão 12).

Rode o backfill manual **antes** do primeiro uso, para que as tabelas de
`resultados/` já nasçam com histórico em vez de um único mês.
