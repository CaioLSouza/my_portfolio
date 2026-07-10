# Pesquisa XP → Power BI (modelo tidy)

Migração da planilha **PA Principal** para um modelo limpo (star schema) no Power BI.
Fim das gambiarras: sem coluna por edição, sem `MATCH` por texto, sem 304 gráficos
estáticos. Atualização mensal = **soltar o Excel do Forms na pasta → Atualizar**.

## Arquivos desta pasta
| Arquivo | O que é |
|---|---|
| `fResponses.csv` | **Fato (tidy)** — 1 linha por *respondente × pergunta × resposta*. Multi-escolha já quebrada em linhas. (~121k linhas, 2020→2026) |
| `dimPergunta.csv` | Dicionário de perguntas: `QuestionID`, `TextoPT`, `Tipo` (única/múltipla/aberta), `ChaveTexto` (p/ casar o Forms). |
| `dimAlternativa.csv` | Dicionário de alternativas: `AnswerID`, `QuestionID`, `RotuloPT`, `RotuloEN`, `Ordem`, `Origem` (curada/auto). |
| `dimPeriodo.csv` | Calendário de edições: `Periodo`, `Data`, `Ano`, `Mes`, `Trimestre`, `Edicao`. |
| `dimRespondente.csv` | 1 linha por respondente: `RespID`, `Periodo`, `Data`, `Regiao`. |
| `_RevisarAlternativas.csv` | Alternativas preenchidas automaticamente (`Origem=auto`) — revise rótulo/EN quando puder. |
| `PowerQuery_NovosForms.pq` | Código M para importar os Forms mensais de uma pasta. |
| `Medidas_DAX.txt` | Medidas prontas (% da resposta etc.). |

## 1. Importar
Power BI Desktop → **Obter Dados → Texto/CSV** → importe os 5 arquivos
(`fResponses`, `dimPergunta`, `dimAlternativa`, `dimPeriodo`, `dimRespondente`).
Confira os tipos: `Periodo` = número inteiro; `Data` = data.
> Dica: no `fResponses`, deixe `RespID` como **Texto** (vai conviver com os IDs
> novos do Forms, que são texto tipo `202607-12`).

## 2. Relacionamentos (Modo Modelo)
Crie (todos 1→* saindo das dimensões para o fato):
- `dimPergunta[QuestionID]` → `fResponses[QuestionID]`
- `dimAlternativa[AnswerID]` → `fResponses[AnswerID]`
- `dimPeriodo[Periodo]` → `fResponses[Periodo]`
- `dimRespondente[RespID]` → `fResponses[RespID]`

Marque `dimPeriodo` como **Tabela de Datas** (campo `Data`).

## 3. Medidas
Cole as de `Medidas_DAX.txt` (principal: **`% da Resposta`**).

## 4. Visuais (exemplos)
- **Slicers:** `dimPergunta[TextoPT]` e `dimPeriodo[Data]`.
- **Barras (mês atual):** Eixo `dimAlternativa[RotuloPT]` · Valor `% da Resposta`.
- **Linha (série histórica):** Eixo `dimPeriodo[Data]` · Legenda `dimAlternativa[RotuloPT]` · Valor `% da Resposta`.
- **Mapa/Barras por região:** use `dimRespondente[Regiao]`.

Um único par de gráficos (barra + linha) + o slicer de pergunta já substitui as
dezenas de gráficos estáticos: troca a pergunta no slicer e tudo reage.

## 5. Atualização mensal (o pulo do gato)
`PowerQuery_NovosForms.pq` define **4 consultas** — crie cada uma em
**Transformar Dados → Nova Consulta → Consulta em Branco → Editor Avançado**,
colando o bloco correspondente e nomeando exatamente como indicado no arquivo:

| Consulta | Para quê |
|---|---|
| `ImportForms_Detalhe` | Lê a pasta, faz o unpivot e o casamento (motor interno). |
| `NovosForms` | Saída limpa (`RespID/Periodo/Data/QuestionID/AnswerRaw`) — é essa que entra no histórico. |
| `_AuditoriaCasamentoParecido` | Perguntas que casaram por **semelhança**, não por texto igual — confira 1x/mês. |
| `_PerguntasNaoReconhecidas` | Perguntas realmente **novas** (não casaram nem exato nem parecido). |

1. Baixe o Excel de respostas no MS Forms e salve numa pasta fixa, com o período
   no nome: **`PA_202607.xlsx`**.
2. Ajuste `PASTA` em `ImportForms_Detalhe`.
3. Crie a consulta final `fResponses` = **combinar** histórico + novos:
   `Table.Combine({ fResponses_Historico, NovosForms })`.
4. Todo mês: jogar o arquivo do Forms na pasta → **Página Inicial → Atualizar** →
   dar uma olhada nas duas consultas `_...` → Fim.

### Por que existe o "match parecido" (fuzzy)
Testei com o export real de **Junho/2026**: das 12 perguntas do mês, **8 casaram
por texto exato** e **4 só casaram por semelhança** — o texto tinha mudado
ligeiramente (ex.: *"qual você acha que deve ser o **maior risco**..."* virou
*"quais você acha que devem ser os **maiores riscos**..."*). Um match só por
texto exato trataria essas 4 como perguntas novas e **fragmentaria o histórico**
em duas séries diferentes para a mesma pergunta. Por isso o motor tenta match
exato primeiro e, só no que sobra, tenta por semelhança (limiar ajustável em
`LIMIAR_PARECIDO`, padrão `0.80`) — e deixa tudo auditável nas duas consultas `_...`.

## 6. Perguntas / alternativas novas
- **Pergunta com texto reformulado:** casa sozinha (fuzzy) — aparece em
  `_AuditoriaCasamentoParecido` só para você confirmar que casou com a certa.
- **Pergunta genuinamente nova:** aparece em `_PerguntasNaoReconhecidas`.
  Adicione 1 linha em `dimPergunta` (novo `QuestionID` + `TextoPT` +
  `ChaveTexto` = texto normalizado) e pronto.
- **Alternativa nova:** aparece nos dados e entra no gráfico automaticamente (o %
  usa `AnswerRaw`). Para rótulo bonito/EN/ordenação, adicione em `dimAlternativa`.

> Curadoria virou **adicionar linha em tabela** — não mais editar blocos de COUNTIFS.

## Observação sobre os %
O `% da Resposta` usa como base os **respondentes que responderam àquela pergunta no
período** (medida `Base da Pergunta`). É mais correto que dividir pelo total do mês
quando a pergunta é opcional/entrou no meio. Para múltipla escolha, a soma passa de
100% (esperado). Se quiser replicar exatamente o denominador antigo (total do mês),
troque a base por `Respondentes no Período`.
