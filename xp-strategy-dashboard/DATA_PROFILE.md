# DATA_PROFILE — Phase 0 discovery (github samples)

Profiled 15 sources via the app's own loader (`DATA_SOURCE=github`). Samples are small extracts; prod parquets may add `(cod_ativo, data)` index columns and far more rows.

## `performance_carteiras`

- **Description:** Historico de composicao e performance das carteiras XP
- **Prod:** `\\xpdocs\Research\Equities\Estrategia\Carteiras\Performance carteiras.xlsm` (xlsm)
- **Sample type:** xlsx
- **Sheets:** Instruções, Lâmina, Performance, Composição, Ranking, Desempenho Ativo, Carteira - TOP Ações XP, Desempenho Top Acoes, Carteira - TOP DIVIDENDOS XP, Desempenho Top Dividendos, Carteira - TOP SMALL CAPS XP, Plan1, Desempenho Top Small Caps, Carteira - ESG XP, Historico, Setores, Auxiliar, Pesos ESG, Individual Sectors, Sector Groups
- **Shape:** 10 rows × 2 cols
- **Date range:** no datetime column detected
- **Tickers:** no ticker column detected
- **Nulls (top):** `Atualizar pesos dos componentes nas abas beiges (Carteria - Top XX XP)` 60%, `Unnamed: 1` 60%
- **Dtypes:** `Atualizar pesos dos componentes nas abas beiges (Carteria - Top XX XP)`: str, `Unnamed: 1`: str

Sample rows:

| Atualizar pesos dos componentes nas abas beiges (Carteria - Top XX XP)                                     | Unnamed: 1                                                                                                                               |
|:-----------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------|
| nan                                                                                                        | nan                                                                                                                                      |
| 1. Há uma aba para cada carteiras (top 10, dividendos, small caps e ESG), para inputar as mudanças mensais | nan                                                                                                                                      |
| Pontos de atenção:                                                                                         | a) para a carteira de cada mês, a data no topo é o fechamento do anterior. Exemplo: Carteira de junho -> a data no topo tem que ser 31/5 |

**Sheet `Instruções`** — 10×2; cols: Atualizar pesos dos componentes nas abas beiges (Carteria - Top XX XP), Unnamed: 1

**Sheet `Lâmina`** — 10×16; cols: Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7, Unnamed: 8, Unnamed: 9, Unnamed: 10, Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

**Sheet `Performance`** — 9×25; cols: Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7, Unnamed: 8, Unnamed: 9, Unnamed: 10, Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

**Sheet `Composição`** — 10×87; cols: 2026-06-30 00:00:00, ← Não modificar célula, Unnamed: 2, Unnamed: 3, Unnamed: 4, RECOMMENDATION, TARGET, Buy, Neutral, Under Review, DY_2026, Restricted, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

**Sheet `Ranking`** — 10×28; cols: Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7, Unnamed: 8, Unnamed: 9, Unnamed: 10, Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

**Sheet `Desempenho Ativo`** — 10×23; cols: Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7, Unnamed: 8, Unnamed: 9, Unnamed: 10, Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

**Sheet `Carteira - TOP Ações XP`** — 10×109; cols: TOP Ações XP                                                                                                     <EcoPortfolio>{"type":"p","tolerance":"15d","rebalance":"YES","name":"TOP Ações XP","data":[["Ticker","2025-02-28","2025-03-31","2025-04-30","2025-05-30","2025-06-30","2025-07-31","2025-08-29","2025-09-30","2025-10-31","2025-11-07","2025-11-28","2025-12-19","2025-12-30","2026-01-31","2026-02-28","2026-03-31","2026-04-30","2026-05-29","2026-06-30",null,null,null,null],["AMER3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["BBAS3",5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["BRFS3",null,5.0,7.5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CMIG4",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["EQTL3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["GGBR4",10.0,5.0,null,null,null,5.0,5.0,null,5.0,5.0,5.0,5.0,5.0,null,null,null,5.0,5.0,5.0,null,null,null,null],["RENT3",null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,5.0,5.0,7.5,7.5,10.0,10.0,null,null,null,null],["SUZB3",5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["TIMS3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["VALE3",10.0,12.5,12.5,12.5,5.0,5.0,5.0,10.0,10.0,10.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null],["B3SA3",5.0,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,5.0,5.0,7.5,5.0,7.5,7.5,null,null,null,null],["FIBR3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["PETR4",12.5,12.5,10.0,10.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,5.0,10.0,10.0,10.0,5.0,5.0,null,null,null,null],["EGIE3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["KLBN11",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["BBDC4",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["UGPA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["BRML3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["AZUL54",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["ITUB4",15.0,15.0,15.0,15.0,10.0,10.0,12.5,15.0,15.0,15.0,15.0,15.0,15.0,15.0,15.0,10.0,10.0,10.0,10.0,null,null,null,null],["JBSS3",5.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["AESB3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["PCAR4",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["LREN3",null,null,5.0,5.0,10.0,10.0,null,null,null,null,null,null,null,null,10.0,10.0,5.0,5.0,5.0,null,null,null,null],["CPLE6",10.0,10.0,10.0,12.5,12.5,12.5,10.0,10.0,10.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["ENBR3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["IRBR3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["IGTA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["ECOR3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["BHIA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["EZTC3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CYRE3",5.0,5.0,2.5,null,null,null,5.0,5.0,10.0,10.0,10.0,10.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null],["VIVA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["ABEV3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["PCAR3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["MBRF3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CESP6",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SRNA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["LAME4",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["LWSA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["MOVI3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["TEND3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CEAB3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["RDOR3",null,null,null,null,null,null,10.0,null,null,null,null,null,null,null,null,null,null,null,7.5,null,null,null,null],["ASAI3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["GNDI3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["MULT3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SULA11",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["AZZA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["WEGE3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SMTO3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["RADL3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,null,null,null,null,null,null],["RAIL3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CBAV3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["HYPE3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["IGTI11",5.0,5.0,5.0,5.0,5.0,5.0,5.0,10.0,10.0,10.0,10.0,10.0,10.0,10.0,10.0,10.0,10.0,10.0,10.0,null,null,null,null],["AUAU3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["RAIZ4",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SOMA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["AXIA3",null,5.0,5.0,10.0,10.0,10.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null],["TOTS3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,2.5,5.0,5.0,null,null,null,null],["PRIO3",null,null,null,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null],["VAMO3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["GMAT3",2.5,2.5,2.5,2.5,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["MDIA3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SBSP3",null,null,null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null],["INBR32",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SMFT3",null,null,null,null,5.0,5.0,5.0,5.0,10.0,10.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null],["NATU3",5.0,2.5,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CXSE3",5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null],["MOTV3",null,5.0,5.0,7.5,7.5,7.5,7.5,10.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null],["STOC34",null,null,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["SANB11",null,null,null,null,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null],["JBSS32",null,null,null,null,null,null,5.0,5.0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["CPLE5",null,null,null,null,null,null,null,null,null,10.0,10.0,null,null,null,null,null,null,null,null,null,null,null,null],["BPAC11",null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null],["AURA33",null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,5.0,5.0,5.0,null,null,null,null,null,null,null],["MELI34",null,null,null,null,null,null,null,null,null,null,5.0,5.0,10.0,10.0,null,null,null,null,null,null,null,null,null],["CPLE3",null,null,null,null,null,null,null,null,null,null,null,10.0,10.0,10.0,10.0,10.0,10.0,10.0,null,null,null,null,null],["ROXO34",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,5.0,null,null,null,null],["EMBJ3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5.0,5.0,5.0,null,null,null,null],["ORVR3",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,2.5,5.0,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],["",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]]}, ., Unnamed: 2, TOP Ações XP, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7, Unnamed: 8, Unnamed: 9, Unnamed: 10, Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

**Sheet `Desempenho Top Acoes`** — 10×92; cols: Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7, Unnamed: 8, Unnamed: 9, Unnamed: 10, Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14 …

## `singlename_flows`

- **Description:** Fluxo por participante por papel da Bolsa (indexado por cod_ativo,data)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\databricks-singlename-flows.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 49 cols
- **Date range:** no datetime column detected
- **Tickers:** no ticker column detected
- **Nulls (top):** `21d_foreigners_flow` 100%, `252d_foreigners_flow_to_ff` 100%, `63d_foreigners_flow` 100%, `252d_foreigners_flow` 100%, `21d_foreigners_flow_to_adtv` 100%, `63d_foreigners_flow_to_adtv` 100%, `252d_foreigners_flow_to_adtv` 100%, `21d_foreigners_flow_to_ff` 100%, `63d_foreigners_flow_to_ff` 100%, `63d_retail_flow_to_adtv` 100%, `21d_retail_flow` 100%, `63d_retail_flow` 100%
- **Dtypes:** `daily_foreigners_flow`: float64, `21d_foreigners_flow`: float64, `63d_foreigners_flow`: float64, `252d_foreigners_flow`: float64, `21d_foreigners_flow_to_adtv`: float64, `63d_foreigners_flow_to_adtv`: float64, `252d_foreigners_flow_to_adtv`: float64, `21d_foreigners_flow_to_ff`: float64, `63d_foreigners_flow_to_ff`: float64, `252d_foreigners_flow_to_ff`: float64, `daily_retail_flow`: int64, `21d_retail_flow`: float64, `63d_retail_flow`: float64, `252d_retail_flow`: float64, `21d_retail_flow_to_adtv`: float64, `63d_retail_flow_to_adtv`: float64, `252d_retail_flow_to_adtv`: float64, `21d_retail_flow_to_ff`: float64, `63d_retail_flow_to_ff`: float64, `252d_retail_flow_to_ff`: float64, `daily_local_institutions_flow`: float64, `21d_local_institutions_flow`: float64, `63d_local_institutions_flow`: float64, `252d_local_institutions_flow`: float64, `21d_local_institutions_flow_to_adtv`: float64, `63d_local_institutions_flow_to_adtv`: float64, `252d_local_institutions_flow_to_adtv`: float64, `21d_local_institutions_flow_to_ff`: float64, `63d_local_institutions_flow_to_ff`: float64, `252d_local_institutions_flow_to_ff`: float64, `daily_others_flow`: float64, `21d_others_flow`: float64, `63d_others_flow`: float64, `252d_others_flow`: float64, `21d_others_flow_to_adtv`: float64, `63d_others_flow_to_adtv`: float64, `252d_others_flow_to_adtv`: float64, `21d_others_flow_to_ff`: float64, `63d_others_flow_to_ff`: float64, `252d_others_flow_to_ff`: float64 … (+9 more)

Sample rows:

|   daily_foreigners_flow |   21d_foreigners_flow |   63d_foreigners_flow |   252d_foreigners_flow |   21d_foreigners_flow_to_adtv |   63d_foreigners_flow_to_adtv |   252d_foreigners_flow_to_adtv |   21d_foreigners_flow_to_ff |   63d_foreigners_flow_to_ff |   252d_foreigners_flow_to_ff |   daily_retail_flow |   21d_retail_flow |
|------------------------:|----------------------:|----------------------:|-----------------------:|------------------------------:|------------------------------:|-------------------------------:|----------------------------:|----------------------------:|-----------------------------:|--------------------:|------------------:|
|        191398           |                   nan |                   nan |                    nan |                           nan |                           nan |                            nan |                         nan |                         nan |                          nan |             -540111 |               nan |
|        291712           |                   nan |                   nan |                    nan |                           nan |                           nan |                            nan |                         nan |                         nan |                          nan |              242956 |               nan |
|             1.90702e+06 |                   nan |                   nan |                    nan |                           nan |                           nan |                            nan |                         nan |                         nan |                          nan |              503442 |               nan |

_(first 12 of 49 columns)_

## `index_composition`

- **Description:** Composicao/peso por papel de indices (IBOV,SMLL,MLCX,IBX50,IBX100)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\economatica-index_composition.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 7 cols
- **Date range:** `data`: 2021-12-30 → 2022-01-13 (10 unique)
- **Tickers:** `cod_ativo`: 1 unique
- **Nulls (top):** `IBOV` 100%, `IBX50` 100%, `MLCX` 100%, `IBX100` 100%
- **Dtypes:** `cod_ativo`: str, `data`: datetime64[us], `IBOV`: float64, `SMLL`: float64, `MLCX`: float64, `IBX50`: float64, `IBX100`: float64

Sample rows:

| cod_ativo   | data                |   IBOV |   SMLL |   MLCX |   IBX50 |   IBX100 |
|:------------|:--------------------|-------:|-------:|-------:|--------:|---------:|
| TTEN3       | 2021-12-30 00:00:00 |    nan |  0.332 |    nan |     nan |      nan |
| TTEN3       | 2022-01-03 00:00:00 |    nan |  0.323 |    nan |     nan |      nan |
| TTEN3       | 2022-01-04 00:00:00 |    nan |  0.331 |    nan |     nan |      nan |

## `market_cap`

- **Description:** Historico de market cap (classe e companhia)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\economatica-market_cap.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 4 cols
- **Date range:** `data`: 2021-07-08 → 2021-07-21 (10 unique)
- **Tickers:** `cod_ativo`: 1 unique
- **Nulls (top):** no nulls
- **Dtypes:** `cod_ativo`: str, `data`: datetime64[us], `market_cap_class`: float64, `market_cap_company`: float64

Sample rows:

| cod_ativo   | data                |   market_cap_class |   market_cap_company |
|:------------|:--------------------|-------------------:|---------------------:|
| TTEN3       | 2021-07-08 00:00:00 |        6.05294e+09 |          6.05294e+09 |
| TTEN3       | 2021-07-09 00:00:00 |        6.05294e+09 |          6.05294e+09 |
| TTEN3       | 2021-07-12 00:00:00 |        5.97882e+09 |          5.97882e+09 |

## `market_data`

- **Description:** Historico de precos OHLCV por acao
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\economatica-market_data.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 11 cols
- **Date range:** `data`: 2021-07-08 → 2021-07-22 (10 unique)
- **Tickers:** `cod_ativo`: 1 unique
- **Nulls (top):** no nulls
- **Dtypes:** `cod_ativo`: str, `data`: datetime64[us], `open_price`: float64, `high_price`: float64, `low_price`: float64, `avg_price`: float64, `close_price`: float64, `adj_close_price`: float64, `trading_volume`: int64, `number_of_trades`: int64, `number_of_shares_traded`: int64

Sample rows:

| cod_ativo   | data                |   open_price |   high_price |   low_price |   avg_price |   close_price |   adj_close_price |   trading_volume |   number_of_trades |   number_of_shares_traded |
|:------------|:--------------------|-------------:|-------------:|------------:|------------:|--------------:|------------------:|-----------------:|-------------------:|--------------------------:|
| TTEN3       | 2021-07-08 00:00:00 |      11.6833 |      11.6833 |     11.6833 |     11.6833 |         12.25 |           11.6833 |                0 |                  0 |                         0 |
| TTEN3       | 2021-07-12 00:00:00 |      12.0171 |      12.3509 |     11.4449 |     11.7119 |         12.1  |           11.5403 |        322286880 |              41175 |                  26228300 |
| TTEN3       | 2021-07-13 00:00:00 |      11.5403 |      11.8073 |     11.4449 |     11.5593 |         12.15 |           11.5879 |         62933885 |               9246 |                   5188700 |

## `short_selling`

- **Description:** Short interest, lending rate, days to cover, free float
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\economatica-short_selling.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 12 cols
- **Date range:** `data`: 2016-11-04 → 2016-11-18 (10 unique)
- **Tickers:** `cod_ativo`: 1 unique
- **Nulls (top):** `surprise_in_si` 100%, `days_to_cover` 100%
- **Dtypes:** `cod_ativo`: str, `data`: datetime64[us], `short_interest`: int64, `avg_shorted_price`: float64, `short_interest_value`: float64, `lending_rate`: float64, `short_interest_pct`: float64, `days_to_cover`: float64, `free_float`: int64, `market_cap_class`: float64, `market_cap_company`: float64, `surprise_in_si`: float64

Sample rows:

| cod_ativo   | data                |   short_interest |   avg_shorted_price |   short_interest_value |   lending_rate |   short_interest_pct |   days_to_cover |   free_float |   market_cap_class |   market_cap_company |   surprise_in_si |
|:------------|:--------------------|-----------------:|--------------------:|-----------------------:|---------------:|---------------------:|----------------:|-------------:|-------------------:|---------------------:|-----------------:|
| AALR3       | 2016-11-04 00:00:00 |             1000 |               17.93 |                  17930 |           1.55 |          6.67965e-05 |             nan |     14970844 |        2.03945e+09 |          2.03945e+09 |              nan |
| AALR3       | 2016-11-07 00:00:00 |             1000 |               17.84 |                  17840 |           1.55 |          6.67965e-05 |             nan |     14970844 |        2.02796e+09 |          2.02796e+09 |              nan |
| AALR3       | 2016-11-08 00:00:00 |             1100 |               17.68 |                  19448 |           1.5  |          7.34762e-05 |             nan |     14970844 |        2.00958e+09 |          2.00958e+09 |              nan |

## `consensus`

- **Description:** Consenso Refinitiv (~86 metricas forward/analistas)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\eikon-consensus.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 86 cols
- **Date range:** no datetime column detected
- **Tickers:** no ticker column detected
- **Nulls (top):** `deposit_growth` 100%, `analyst_revision_rec_momentum_63d` 100%, `revenue_fwd_growth` 100%, `revenues_fwd_growth` 100%, `analyst_revisions_netincome_momentum_63d_blended` 100%, `analyst_revisions_rec_momentum_63d` 100%, `long_term_growth` 100%, `ebitda_fwd` 100%, `analyst_revisions_sales_momentum_126d_fy1` 100%, `analyst_revisions_ebitda_momentum_63d_blended` 100%, `analyst_rec` 100%, `analyst_number_earnings` 100%
- **Dtypes:** `deposit_growth`: float64, `analyst_revision_rec_momentum_63d`: float64, `revenue_fwd_growth`: float64, `revenues_fwd_growth`: float64, `analyst_revisions_netincome_momentum_63d_blended`: float64, `analyst_revisions_rec_momentum_63d`: float64, `long_term_growth`: float64, `ebitda_fwd`: float64, `analyst_revisions_sales_momentum_126d_fy1`: float64, `analyst_revisions_ebitda_momentum_63d_blended`: float64, `analyst_rec`: float64, `analyst_number_earnings`: float64, `analyst_revisions_sales_momentum_63d_fy2`: float64, `analyst_revisions_sales_momentum_63d_blended`: float64, `analyst_growth_netincome_1y`: float64, `peg_fwd`: float64, `analyst_growth_sales_2y`: float64, `analyst_revisions_netincome_momentum_63d_fy1`: float64, `sales_fy0`: int64, `ebitda_fy0`: float64, `roic_fwd`: float64, `ebitda_fwd_growth`: float64, `analyst_revisions_sales_momentum_252d_blended`: float64, `netincome_fy1`: int64, `refinitiv_market_cap_free_float`: float64, `analyst_revisions_netincome_momentum_252d_fy1`: float64, `net_debt_fwd`: float64, `analyst_revisions_ebitda_momentum_126d_fy1`: float64, `analyst_revisions_ebitda_momentum_252d_fy1`: float64, `analyst_revisions_netincome_momentum_252d_blended`: float64, `wacc`: float64, `sales_fy1`: float64, `analyst_revision_rec_momentum_126d`: float64, `free_cash_flow_fwd`: float64, `sales_fy2`: float64, `net_income_fwd`: float64, `analyst_revisions_sales_momentum_252d_fy2`: float64, `ev_fwd`: float64, `analyst_revisions_sales_momentum_63d_fy1`: float64, `analyst_revisions_ebitda_momentum_126d_fy2`: float64 … (+46 more)

Sample rows:

|   deposit_growth |   analyst_revision_rec_momentum_63d |   revenue_fwd_growth |   revenues_fwd_growth |   analyst_revisions_netincome_momentum_63d_blended |   analyst_revisions_rec_momentum_63d |   long_term_growth |   ebitda_fwd |   analyst_revisions_sales_momentum_126d_fy1 |   analyst_revisions_ebitda_momentum_63d_blended |   analyst_rec |   analyst_number_earnings |
|-----------------:|------------------------------------:|---------------------:|----------------------:|---------------------------------------------------:|-------------------------------------:|-------------------:|-------------:|--------------------------------------------:|------------------------------------------------:|--------------:|--------------------------:|
|              nan |                                 nan |                  nan |                   nan |                                                nan |                                  nan |                nan |          nan |                                         nan |                                             nan |           nan |                       nan |
|              nan |                                 nan |                  nan |                   nan |                                                nan |                                  nan |                nan |          nan |                                         nan |                                             nan |           nan |                       nan |
|              nan |                                 nan |                  nan |                   nan |                                                nan |                                  nan |                nan |          nan |                                         nan |                                             nan |           nan |                       nan |

_(first 12 of 86 columns)_

## `factor_zoo`

- **Description:** Master single-name (~322 colunas) indexado por cod_ativo,data
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\factor_zoo.parquet` (parquet)
- **Sample type:** xlsx
- **Shape:** 10 rows × 322 cols
- **Date range:** no datetime column detected
- **Tickers:** no ticker column detected
- **Nulls (top):** `252d_diff_local_institutions_foreigners_flow_to_ff` 100%, `63d_foreigners_flow_to_ff` 100%, `252d_foreigners_flow_to_ff` 100%, `daily_retail_flow` 100%, `21d_retail_flow` 100%, `63d_retail_flow` 100%, `252d_retail_flow` 100%, `21d_retail_flow_to_adtv` 100%, `63d_retail_flow_to_adtv` 100%, `daily_foreigners_flow` 100%, `21d_foreigners_flow` 100%, `63d_foreigners_flow` 100%
- **Dtypes:** `open_price`: float64, `high_price`: float64, `low_price`: float64, `avg_price`: float64, `close_price`: float64, `adj_close_price`: float64, `trading_volume`: float64, `number_of_trades`: int64, `number_of_shares_traded`: float64, `50d_ma`: float64, `200d_ma`: float64, `rsi`: float64, `stoch`: float64, `macd`: float64, `21d_average_dollar_volume_traded`: float64, `21d_average_volume_traded`: float64, `63d_average_dollar_volume_traded`: float64, `63d_average_volume_traded`: float64, `252d_average_dollar_volume_traded`: float64, `252d_average_volume_traded`: float64, `21d_share_turnover_free_float`: float64, `63d_share_turnover_free_float`: float64, `252d_share_turnover_free_float`: float64, `21d_share_turnover_outstanding`: float64, `63d_share_turnover_outstanding`: float64, `252d_share_turnover_outstanding`: float64, `sales_growth_volatility`: float64, `ebitda_growth_volatility`: float64, `earnings_growth_volatility`: float64, `sales_variability`: float64, `earnings_variability`: float64, `ebitda_variability`: float64, `roe_variability`: float64, `ebitda_margin_variability`: float64, `gross_margin_variability`: float64, `gross_margin_growth`: float64, `ebit_margin_growth`: float64, `ebitda_margin_growth`: float64, `net_margin_growth`: float64, `fcf_margin_growth`: float64 … (+282 more)

Sample rows:

|   open_price |   high_price |   low_price |   avg_price |   close_price |   adj_close_price |   trading_volume |   number_of_trades |   number_of_shares_traded |   50d_ma |   200d_ma |     rsi |
|-------------:|-------------:|------------:|------------:|--------------:|------------------:|-----------------:|-------------------:|--------------------------:|---------:|----------:|--------:|
|     1.25917  |     1.25917  |    1.23934  |    1.23934  |        1.25   |          1.23934  |      3.19461e+06 |                113 |                 2.548e+06 | 0.913807 |  0.829297 | 83.74   |
|     2.04035  |     2.08901  |    2.04035  |    2.07131  |        0.0425 |          2.08901  | 210710           |                  5 |             10000         | 1.74577  |  1.60298  | 67.8809 |
|     0.149345 |     0.149345 |    0.149345 |    0.149345 |        7e-05  |          0.149345 |    700           |                  1 |               290         | 0.131147 |  0.141602 | 55.8261 |

_(first 12 of 322 columns)_

## `sector_classification`

- **Description:** Taxonomia setorial XP (chave cod_ativo)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\xpqs-sector_classification.xlsx` (xlsx)
- **Sample type:** xlsx
- **Sheets:** Cadastro, Planilha1, De Para
- **Shape:** 10 rows × 16 cols
- **Date range:** no datetime column detected
- **Tickers:** `cod_ativo`: 10 unique
- **Nulls (top):** `isin` 50%, `activity` 50%, `ric_code` 10%
- **Dtypes:** `cod_ativo`: str, `cod_cvm`: int64, `cnpj`: int64, `isin`: str, `ric_code`: str, `type`: str, `name`: str, `GICS_sector`: str, `adjusted_GICS_sector`: str, `macro_sector_xp`: str, `sector_xp`: str, `sector_layer_1`: str, `sector_layer_2`: str, `sector_layer_3`: str, `super_sector_xp`: str, `activity`: str

Sample rows:

| cod_ativo   |   cod_cvm |           cnpj | isin         | ric_code     | type   | name       | GICS_sector   | adjusted_GICS_sector   | macro_sector_xp   | sector_xp   | sector_layer_1   |
|:------------|----------:|---------------:|:-------------|:-------------|:-------|:-----------|:--------------|:-----------------------|:------------------|:------------|:-----------------|
| AALR3       |      2405 | 42771949000135 | BRAALRACNOR6 | AALR3.SA     | ON     | Alliar     | Health Care   | Health Care            | Health Care       | Health Care | Health Care      |
| ABCB11      |      2095 | 28195667000106 | nan          | nan          | Units  | ABC Brasil | Financials    | Financials             | Banks             | Banks       | Banks            |
| ABCB3       |      2095 | 28195667000106 | BRABCBACNOR7 | ABCB3.SA^C15 | ON     | ABC Brasil | Financials    | Financials             | Banks             | Banks       | Banks            |

_(first 12 of 16 columns)_

**Sheet `Cadastro`** — 10×16; cols: cod_ativo, cod_cvm, cnpj, isin, ric_code, type, name, GICS_sector, adjusted_GICS_sector, macro_sector_xp, sector_xp, sector_layer_1, sector_layer_2, sector_layer_3, super_sector_xp …

**Sheet `Planilha1`** — 8×0; cols: 

**Sheet `De Para`** — 10×6; cols: ENG, PORT, SECTOR, SUPER SECTOR, SECTOR.1, SECTOR_LAYER_3

## `investors_participation`

- **Description:** Fluxo consolidado a vista por participante
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\b3\b3-investors_participation.xlsx` (xlsx)
- **Sample type:** xlsx
- **Sheets:** Cumulative, Daily
- **Shape:** 10 rows × 21 cols
- **Date range:** `date`: 2023-04-20 → 2023-05-05 (10 unique)
- **Tickers:** no ticker column detected
- **Nulls (top):** no nulls
- **Dtypes:** `date`: datetime64[us], `institutional_investors_purchases`: int64, `financial_institutions_purchases`: int64, `foreign_investors_purchases`: int64, `individual_investors_purchases`: int64, `others_purchases`: int64, `institutional_investors_purchases_part`: float64, `financial_institutions_purchases_part`: float64, `foreign_investors_purchases_part`: float64, `individual_investors_purchases_part`: float64, `others_purchases_part`: float64, `institutional_investors_sales`: int64, `financial_institutions_sales`: int64, `foreign_investors_sales`: int64, `individual_investors_sales`: int64, `others_sales`: int64, `institutional_investors_sales_part`: float64, `financial_institutions_sales_part`: float64, `foreign_investors_sales_part`: float64, `individual_investors_sales_part`: float64, `others_sales_part`: float64

Sample rows:

| date                |   institutional_investors_purchases |   financial_institutions_purchases |   foreign_investors_purchases |   individual_investors_purchases |   others_purchases |   institutional_investors_purchases_part |   financial_institutions_purchases_part |   foreign_investors_purchases_part |   individual_investors_purchases_part |   others_purchases_part |   institutional_investors_sales |
|:--------------------|------------------------------------:|-----------------------------------:|------------------------------:|---------------------------------:|-------------------:|-----------------------------------------:|----------------------------------------:|-----------------------------------:|--------------------------------------:|------------------------:|--------------------------------:|
| 2023-04-20 00:00:00 |                            93678217 |                           11860346 |                     189035595 |                         41554571 |            3232988 |                                   0.138  |                                  0.0175 |                             0.2785 |                                0.0612 |                  0.0048 |                        98528424 |
| 2023-04-24 00:00:00 |                            97781102 |                           12519182 |                     201144121 |                         44418176 |            3345971 |                                   0.1361 |                                  0.0174 |                             0.28   |                                0.0618 |                  0.0047 |                       103892150 |
| 2023-04-25 00:00:00 |                           103102608 |                           13345603 |                     212395424 |                         47454461 |            3515964 |                                   0.1357 |                                  0.0176 |                             0.2796 |                                0.0625 |                  0.0046 |                       109147672 |

_(first 12 of 21 columns)_

**Sheet `Cumulative`** — 10×21; cols: date, institutional_investors_purchases, financial_institutions_purchases, foreign_investors_purchases, individual_investors_purchases, others_purchases, institutional_investors_purchases_part, financial_institutions_purchases_part, foreign_investors_purchases_part, individual_investors_purchases_part, others_purchases_part, institutional_investors_sales, financial_institutions_sales, foreign_investors_sales, individual_investors_sales …

**Sheet `Daily`** — 10×21; cols: date, institutional_investors_purchases, financial_institutions_purchases, foreign_investors_purchases, individual_investors_purchases, others_purchases, institutional_investors_purchases_part, financial_institutions_purchases_part, foreign_investors_purchases_part, individual_investors_purchases_part, others_purchases_part, institutional_investors_sales, financial_institutions_sales, foreign_investors_sales, individual_investors_sales …

## `factor_returns`

- **Description:** Indices de retorno dos fatores XP (~173 fatores)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\factor_output\factor_returns.xlsx` (xlsx)
- **Sample type:** xlsx
- **Sheets:** Top, Bottom, LS
- **Shape:** 10 rows × 173 cols
- **Date range:** `data`: 2008-01-30 → 2008-02-14 (10 unique)
- **Tickers:** no ticker column detected
- **Nulls (top):** `value/ebitda_yield_10y_percentile-unconstrained-ALL` 100%, `value/earnings_yield_10y_percentile-ALL` 100%, `value/timeseries_value-ALL` 100%, `value/ebitda_yield_10y_percentile-ALL` 100%, `short_interest/short_interest_pct_1m_slow_growth-ALL` 100%, `short_interest/composite_daily-ALL` 100%, `short_interest/short_interest_pct-unconstrained-ALL` 100%, `sellside_revisions/ebitda_composite-ALL` 100%, `sellside_revisions/sales_composite-ALL` 100%, `sellside_revisions/sellside_revisions_daily-ALL` 100%, `sellside_revisions/earnings_composite-ALL` 100%, `sellside_revisions/composite-ALL` 100%
- **Dtypes:** `data`: datetime64[us], `momentum/9m1_momentum-unconstrained-ALL`: float64, `momentum/3m_momentum-ALL`: float64, `momentum/9m_momentum-ALL`: float64, `momentum/price_momentum-ALL`: float64, `momentum/12m1_momentum-ALL`: float64, `momentum/12m1_momentum-unconstrained-ALL`: float64, `momentum/12m_momentum-ALL`: float64, `momentum/price_range-unconstrained-ALL`: float64, `momentum/6m1_momentum-ALL`: float64, `momentum/6m_momentum-unconstrained-ALL`: float64, `momentum/3m_momentum-unconstrained-ALL`: float64, `momentum/3m1_momentum-unconstrained-ALL`: float64, `momentum/12m_momentum-unconstrained-ALL`: float64, `momentum/price_momentum-unconstrained-ALL`: float64, `momentum/11m_momentum-ALL`: float64, `momentum/9m1_momentum-ALL`: float64, `momentum/lagged_price_momentum-unconstrained-ALL`: float64, `momentum/11m_momentum-unconstrained-ALL`: float64, `momentum/price_range-ALL`: float64, `momentum/6m1_momentum-unconstrained-ALL`: float64, `momentum/lagged_price_momentum-ALL`: float64, `momentum/1m_momentum-ALL`: float64, `momentum/1m_momentum-unconstrained-ALL`: float64, `momentum/3m1_momentum-ALL`: float64, `momentum/9m_momentum-unconstrained-ALL`: float64, `momentum/6m_momentum-ALL`: float64, `value/ebitda_yield_10y_percentile-unconstrained-ALL`: float64, `value/earnings_yield_ltm-unconstrained-ALL`: float64, `value/book_yield_10y_percentile-ALL`: int64, `value/timeseries_value-unconstrained-ALL`: int64, `value/composite-unconstrained-ALL`: float64, `value/composite-ALL`: float64, `value/timeseries_value-ALL`: float64, `value/earnings_yield_10y_percentile-ALL`: float64, `value/dividend_yield_ltm-ALL`: float64, `value/book_yield_ltm-unconstrained-ALL`: float64, `value/fcf_yield_ltm-ALL`: float64, `value/book_yield_10y_percentile-unconstrained-ALL`: float64, `value/ebitda_yield_ltm-unconstrained-ALL`: float64 … (+133 more)

Sample rows:

| data                |   momentum/9m1_momentum-unconstrained-ALL |   momentum/3m_momentum-ALL |   momentum/9m_momentum-ALL |   momentum/price_momentum-ALL |   momentum/12m1_momentum-ALL |   momentum/12m1_momentum-unconstrained-ALL |   momentum/12m_momentum-ALL |   momentum/price_range-unconstrained-ALL |   momentum/6m1_momentum-ALL |   momentum/6m_momentum-unconstrained-ALL |   momentum/3m_momentum-unconstrained-ALL |
|:--------------------|------------------------------------------:|---------------------------:|---------------------------:|------------------------------:|-----------------------------:|-------------------------------------------:|----------------------------:|-----------------------------------------:|----------------------------:|-----------------------------------------:|-----------------------------------------:|
| 2008-01-30 00:00:00 |                                  1        |                   1        |                    1       |                      1        |                     1        |                                   1        |                    1        |                                 1        |                     1       |                                  1       |                                  1       |
| 2008-01-31 00:00:00 |                                  0.998531 |                   0.999522 |                    1.00413 |                      0.999203 |                     0.986926 |                                   0.986009 |                    0.996187 |                                 0.999014 |                     0.99232 |                                  1.00484 |                                  1.00178 |
| 2008-02-01 00:00:00 |                                  1.01509  |                   1.01591  |                    1.01596 |                      1.01333  |                     1.00264  |                                   1.00347  |                    1.01127  |                                 1.02066  |                     1.00904 |                                  1.0274  |                                  1.01527 |

_(first 12 of 173 columns)_

**Sheet `Top`** — 10×173; cols: data, momentum/9m1_momentum-unconstrained-ALL, momentum/3m_momentum-ALL, momentum/9m_momentum-ALL, momentum/price_momentum-ALL, momentum/12m1_momentum-ALL, momentum/12m1_momentum-unconstrained-ALL, momentum/12m_momentum-ALL, momentum/price_range-unconstrained-ALL, momentum/6m1_momentum-ALL, momentum/6m_momentum-unconstrained-ALL, momentum/3m_momentum-unconstrained-ALL, momentum/3m1_momentum-unconstrained-ALL, momentum/12m_momentum-unconstrained-ALL, momentum/price_momentum-unconstrained-ALL …

**Sheet `Bottom`** — 10×173; cols: data, momentum/9m1_momentum-unconstrained-ALL, momentum/3m_momentum-ALL, momentum/9m_momentum-ALL, momentum/price_momentum-ALL, momentum/12m1_momentum-ALL, momentum/12m1_momentum-unconstrained-ALL, momentum/12m_momentum-ALL, momentum/price_range-unconstrained-ALL, momentum/6m1_momentum-ALL, momentum/6m_momentum-unconstrained-ALL, momentum/3m_momentum-unconstrained-ALL, momentum/3m1_momentum-unconstrained-ALL, momentum/12m_momentum-unconstrained-ALL, momentum/price_momentum-unconstrained-ALL …

**Sheet `LS`** — 10×173; cols: data, momentum/9m1_momentum-unconstrained-ALL, momentum/3m_momentum-ALL, momentum/9m_momentum-ALL, momentum/price_momentum-ALL, momentum/12m1_momentum-ALL, momentum/12m1_momentum-unconstrained-ALL, momentum/12m_momentum-ALL, momentum/price_range-unconstrained-ALL, momentum/6m1_momentum-ALL, momentum/6m_momentum-unconstrained-ALL, momentum/3m_momentum-unconstrained-ALL, momentum/3m1_momentum-unconstrained-ALL, momentum/12m_momentum-unconstrained-ALL, momentum/price_momentum-unconstrained-ALL …

## `bdr_market_data`

- **Description:** Precos historicos de BDRs (ticker tipo MMMC34<XBSP>)
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\raw\bdr_market_data.csv` (csv)
- **Sample type:** csv, csv sep `,`
- **Shape:** 10 rows × 11 cols
- **Date range:** `Data`: 2012-05-18 → 2012-05-31 (10 unique)
- **Tickers:** no ticker column detected
- **Nulls (top):** no nulls
- **Dtypes:** `Ativo`: str, `Data`: datetime64[us], `open_price`: str, `high_price`: str, `low_price`: str, `avg_price`: str, `close_price`: str, `adj_close_price`: str, `trading_volume`: str, `number_of_trades`: str, `number_of_shares_traded`: str

Sample rows:

| Ativo        | Data                |   open_price |   high_price |   low_price |   avg_price |   close_price |   adj_close_price |   trading_volume |   number_of_trades |   number_of_shares_traded |
|:-------------|:--------------------|-------------:|-------------:|------------:|------------:|--------------:|------------------:|-----------------:|-------------------:|--------------------------:|
| MMMC34<XBSP> | 2012-05-18 00:00:00 |      26.6126 |      26.6126 |     26.6126 |     26.6126 |         42.2  |           26.6126 |          1810380 |                  1 |                     42900 |
| MMMC34<XBSP> | 2012-05-21 00:00:00 |      27.1549 |      27.1549 |     27.1549 |     27.1549 |         43.06 |           27.1549 |             4306 |                  1 |                       100 |
| MMMC34<XBSP> | 2012-05-22 00:00:00 |      27.4829 |      27.4829 |     27.4829 |     27.4829 |         43.58 |           27.4829 |             4358 |                  1 |                       100 |

## `comp_sheet`

- **Description:** Estimativas e recomendacoes dos analistas XP (COMP SHEET)
- **Prod:** `\\xpdocs\Research\Equities\COMP SHEET\raw_data.xlsx` (xlsx)
- **Sample type:** xlsx
- **Shape:** 10 rows × 1456 cols
- **Date range:** `PDATE`: 2023-09-27 → 2026-06-02 (9 unique)
- **Tickers:** `TICKER`: 10 unique
- **Nulls (top):** `EBIT_2021` 100%, `EBITDA_ADJ_XP_2029` 100%, `EBITDA_ADJ_XP_2030` 100%, `GROSS_DEBT_2T24` 100%, `NET_DEBT_2T24` 100%, `CAPEX_2T24` 100%, `DIVIDENDS_2T24` 100%, `NET_REV_3Q28` 100%, `NET_INT_INCOME_3Q28` 100%, `CREDIT_COST_3Q28` 100%, `EBIT_3Q28` 100%, `NET_INCOME_3Q28` 100%
- **Dtypes:** `TICKER`: str, `NAME`: str, `SECTOR_XP`: str, `LEAD_ANALYST`: str, `PDATE`: datetime64[us], `RECOMMENDATION`: str, `RESTRICTED`: bool, `MODEL_CURRENCY`: str, `PRICE_CURRENCY`: str, `TARGET`: float64, `KE`: float64, `KD`: float64, `WACC`: float64, `NET_REV_2021`: float64, `GROSS_PROFIT_2021`: float64, `EBIT_2021`: float64, `EBITDA_2021`: float64, `EBITDA_ADJ_2021`: float64, `NET_INCOME_2021`: float64, `NOSH_2021`: float64, `TOTAL_ASSETS_2021`: float64, `CASH_EQUIV_2021`: float64, `PP_E_2021`: float64, `TOTAL_LIAB_2021`: float64, `SHAREHOLDERS_EQUITY_2021`: float64, `GROSS_DEBT_2021`: float64, `NET_DEBT_2021`: float64, `CAPEX_2021`: float64, `FCFF_2021`: float64, `FCFE_2021`: float64, `DIVIDENDS_2021`: float64, `NET_REV_2022`: float64, `GROSS_PROFIT_2022`: float64, `EBIT_2022`: float64, `EBITDA_2022`: float64, `EBITDA_ADJ_2022`: float64, `NET_INCOME_2022`: float64, `NOSH_2022`: float64, `TOTAL_ASSETS_2022`: float64, `CASH_EQUIV_2022`: float64 … (+1416 more)

Sample rows:

| TICKER   | NAME       | SECTOR_XP        | LEAD_ANALYST      | PDATE               | RECOMMENDATION   | RESTRICTED   | MODEL_CURRENCY   | PRICE_CURRENCY   |   TARGET |       KE |          KD |
|:---------|:-----------|:-----------------|:------------------|:--------------------|:-----------------|:-------------|:-----------------|:-----------------|---------:|---------:|------------:|
| ABEV3    | Ambev      | Food & Beverages | Leonardo Alencar  | 2026-04-07 00:00:00 | Sell             | False        | BRL              | BRL              |     13   | 0.14845  |   0.086831  |
| AGBK     | Agibank    | Banks            | Bernardo Guttmann | 2026-06-02 00:00:00 | Buy              | False        | BRL              | USD              |     13   | 0.173752 | nan         |
| AGRO3    | BrasilAgro | Agribusiness     | Leonardo Alencar  | 2026-03-31 00:00:00 | Neutral          | False        | BRL              | BRL              |     22.5 | 0.136575 |   0.0970888 |

_(first 12 of 1456 columns)_

## `sector_index`

- **Description:** Performance historica setorial do Ibovespa (value-weighted)
- **Prod:** `\\xpdocs\Research\Equities\Quant\Setorial\Raw\IBOV_MACRO_SECTOR_VALUE_WEIGHTED_INDEX.xlsx` (xlsx)
- **Sample type:** xlsx
- **Shape:** 10 rows × 16 cols
- **Date range:** `data`: 2000-01-03 → 2000-01-14 (10 unique)
- **Tickers:** no ticker column detected
- **Nulls (top):** `Retail` 100%, `Real Estate` 100%, `Education` 100%, `Transportation` 100%, `Health Care` 100%
- **Dtypes:** `data`: datetime64[us], `Utilities`: float64, `Real Estate`: float64, `Retail`: float64, `Metals & Mining`: float64, `Agri, Food & Beverages`: float64, `Education`: float64, `Pulp & Paper`: float64, `Transportation`: float64, `Financials Non-Banks`: float64, `Banks`: float64, `TMT`: float64, `Oil, Gas & Petrochemicals`: float64, `Capital Goods`: float64, `Health Care`: float64, `Ibovespa`: float64

Sample rows:

| data                |   Utilities |   Real Estate |   Retail |   Metals & Mining |   Agri, Food & Beverages |   Education |   Pulp & Paper |   Transportation |   Financials Non-Banks |   Banks |     TMT |
|:--------------------|------------:|--------------:|---------:|------------------:|-------------------------:|------------:|---------------:|-----------------:|-----------------------:|--------:|--------:|
| 2000-01-03 00:00:00 |     1       |           nan |      nan |          1        |                 1        |         nan |        1       |              nan |                1       | 1       | 1       |
| 2000-01-04 00:00:00 |     1       |           nan |      nan |          1        |                 1        |         nan |        1       |              nan |                1       | 1       | 1       |
| 2000-01-05 00:00:00 |     1.01286 |           nan |      nan |          0.998443 |                 0.983689 |         nan |        1.01461 |              nan |                1.07143 | 1.03225 | 1.03517 |

_(first 12 of 16 columns)_

## `future_flows`

- **Description:** Fluxo consolidado no mercado de futuros por participante
- **Prod:** `\\xpdocs\Research\Equities\Quant\_Cross Data\raw\databricks-future-flows.csv` (csv)
- **Sample type:** csv, csv sep `;`
- **Shape:** 10 rows × 8 cols
- **Date range:** `data_pregao`: 2022-07-13 → 2022-08-02 (9 unique)
- **Tickers:** no ticker column detected
- **Nulls (top):** no nulls
- **Dtypes:** `data_pregao`: datetime64[us], `macro_produto`: str, `categoria_investidor`: str, `QTD`: int64, `CAPT_LIQ`: float64, `COMPRA`: float64, `VENDA`: float64, `VOL_NEGOCIADO`: float64

Sample rows:

| data_pregao         | macro_produto   | categoria_investidor   |   QTD |     CAPT_LIQ |      COMPRA |       VENDA |   VOL_NEGOCIADO |
|:--------------------|:----------------|:-----------------------|------:|-------------:|------------:|------------:|----------------:|
| 2022-07-13 00:00:00 | FUTURO          | FUNDOS                 |   160 |  9.49557e+07 | 3.33956e+10 | 3.33007e+10 |     6.66963e+10 |
| 2022-07-13 00:00:00 | FUTURO          | INSTITUICAO FINANCEIRA |    43 | -6.28173e+06 | 4.98415e+09 | 4.99043e+09 |     9.97458e+09 |
| 2022-07-14 00:00:00 | FUTURO          | PESSOA FISICA          |   111 |  3.66179e+08 | 1.18209e+11 | 1.17843e+11 |     2.36051e+11 |
