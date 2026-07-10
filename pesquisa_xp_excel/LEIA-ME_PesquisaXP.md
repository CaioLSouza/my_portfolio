# Pesquisa XP — Atualização mensal automatizada (`mdlPesquisaXP.bas`)

Macro de 1 clique para atualizar a planilha **PA Principal** todo mês, **sem recriar
nenhum dos 304 gráficos** e sem mexer na curadoria. Os gráficos da aba `Charts` já são
alimentados por fórmula a partir da aba `Base` — esta macro só automatiza o que
alimenta essa base; os gráficos em si continuam exatamente os mesmos, só passam a
enxergar o mês novo automaticamente.

## O que a macro faz
1. **Importa** o export `.xlsx` do MS Forms para a aba **Raw Data**, casando cada
   coluna pelo **texto da pergunta** (colunas 1–5 — Id/início/conclusão/email/nome —
   por posição; perguntas da coluna 6 em diante por texto). Já preenche o **período**
   (coluna A, formato `AAAAMM`).
2. Se o texto exato não bater, tenta casar por **semelhança** (mesma pergunta com
   redação levemente diferente, ex.: *"qual...maior risco"* → *"quais...maiores
   riscos"*) — evita que uma reformulação de enunciado no Forms fragmente o
   histórico daquela pergunta em duas colunas diferentes.
3. **Perguntas genuinamente novas** (nem texto exato, nem parecido) são adicionadas
   como novas colunas no fim do Raw Data e **listadas no log**.
4. **Cria a coluna de edição** na aba **Base** (copia a última coluna viva e ajusta
   `período` / `total de respostas` / `data` / `nome da edição`) — acabou o
   "arrastar as fórmulas pra direita". Os 304 gráficos da aba `Charts` **não são
   tocados**; eles leem essa base e se atualizam sozinhos.
5. **Atualiza o ponteiro de data** da aba **Charts** para a edição nova.
6. Gera a aba **`_Log Atualizacao`** com:
   - **Perguntas novas** (falta criar o bloco na Base);
   - **Perguntas casadas por semelhança** (confira se casou com a certa);
   - **Alternativas novas/alteradas** — respostas que aparecem no mês mas ainda não
     estão na lista de alternativas da Base (ex.: "ETF", "UCITS", "Fundos Renda +").

> A macro **não** cria sozinha os blocos de perguntas novas nem apaga alternativas —
> isso continua sob seu controle (a curadoria e os gráficos são sensíveis). Ela
> **faz o trabalho repetitivo e te entrega a lista exata do que revisar.**

**Testado contra o export real do MS Forms de Junho/2026:** das 12 perguntas do mês,
8 casaram por texto exato e 4 por semelhança (96–99%) — **12/12 casaram, 0 pergunta
nova, 0 resposta perdida.**

## Configuração — só na 1ª vez
1. Abra `PA_Principal.xlsx`.
2. `Alt+F11` → **Arquivo → Importar Arquivo…** → selecione **`mdlPesquisaXP.bas`**.
3. **Salve como** `Pasta de Trabalho Habilitada para Macro (*.xlsm)`.
4. (Opcional) crie um botão na aba `Summary` e atribua a macro `AtualizarPesquisa`.

## Uso mensal
1. Baixe o Excel de respostas no MS Forms.
2. `Alt+F8` → **`AtualizarPesquisa`** → informe o **período** (`AAAAMM`) → escolha o
   arquivo do Forms → confira o **plano** (nº de respostas, perguntas novas, coluna
   de edição) → **Confirmar**.
3. Revise a aba **`_Log Atualizacao`**: crie na Base os blocos de perguntas novas e
   ajuste alternativas, se houver.
4. Salve uma cópia na pasta do mês.

## Recomendações
- **Teste primeiro numa cópia** do arquivo (não dá pra testar macro contra o seu
  Forms real fora do seu ambiente). O passo de **confirmação** mostra o plano antes
  de gravar qualquer coisa.
- Se a macro marcar como "pergunta nova" algo que já existia, é sinal de que o
  **texto no Forms mudou** em relação ao cabeçalho no Raw Data — basta padronizar o
  texto (o casamento é por texto normalizado: ignora maiúsc./minúsc., espaços e
  espaços não-quebráveis).

## Ajustes fáceis (topo do módulo)
- `RAW_FIRST_QCOL` (padrão `6`/F) — primeira coluna de pergunta no Raw Data.
- `LEADING_COLS` (padrão `5`) — colunas fixas do Forms mapeadas por posição.
- `RAW_PERIOD_COL` (padrão `1`/A) — coluna do código do período.
- `LIMIAR_PARECIDO` (padrão `0.85`) — quão parecido o texto precisa ser pra casar
  automaticamente (0 a 1). Se a macro deixar passar uma pergunta errada como
  "parecida", suba o valor; se estiver perdendo reformulações reais, desça um pouco.

Campos e nomes de aba (`Raw Data`, `Base`, `Charts`) também são constantes no topo.

## Esta macro vs. a migração para Power BI
Este projeto também tem um pacote de migração para **Power BI** (pasta
`pesquisa_xp_powerbi/`), útil se você quiser abandonar os 304 gráficos por
visuais dinâmicos/parametrizados. Esta macro (`mdlPesquisaXP.bas`) é o caminho
para quem **quer manter os gráficos do Excel como estão** — as duas soluções usam
a mesma lógica de casamento de pergunta (exato + semelhança), só que uma dentro
do Excel/VBA e outra no Power Query/M.
