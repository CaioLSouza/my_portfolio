# Raio-XP da Bolsa — P/E 12m fwd. por Setor (Bloomberg)

Planilha reconstruída do zero para gerar as tabelas de **P/E projetado (12 meses)**
por setor MSCI, em **português e inglês**, com as **barras de faixa (mín–máx)**
desenhadas por macro. / *Rebuilt-from-scratch workbook that produces 12M forward
P/E tables by MSCI sector, in Portuguese and English, with macro-drawn range bars.*

## Arquivos / Files
- `RaioXP_PE_por_Setor.xlsx` — a planilha (engine + tabelas EN/PT).
- `mdlRaioXP.bas` — o módulo VBA (a macro).

---

## Configuração — só na 1ª vez / One-time setup
1. Abra `RaioXP_PE_por_Setor.xlsx` em um PC com o **Terminal Bloomberg** (add-in BDH ativo).
2. `Alt+F11` → menu **Arquivo → Importar Arquivo…** → selecione **`mdlRaioXP.bas`**.
3. Na aba **Painel**, clique com o botão direito no botão vermelho **ATUALIZAR** →
   **Atribuir Macro** → **`AtualizarTudo`**. *(ou rode por `Alt+F8`)*
4. Salve como **Pasta de Trabalho Habilitada para Macro (`*.xlsm`)**.

## Uso mensal / Monthly use
1. Na aba **Painel**, ajuste a **data de fechamento** em `C4` (padrão = último mês).
2. Clique em **ATUALIZAR** (ou `Alt+F8` → `AtualizarTudo`).
3. Pronto: a macro puxa 10 anos de histórico via Bloomberg, congela em valores,
   recalcula e monta as abas **Consolidated / Consolidado (PT) / Relative / Relativo (PT)**
   com as barras. Carimba a data/hora no `Painel!C8`.

---

## O que a macro faz / What the macro does
- **`AtualizarTudo`** — fluxo completo de 1 clique (recomendado).
- **`AtualizarBloomberg_Somente`** — só refresca o Bloomberg e redesenha as barras,
  **sem** congelar o histórico (útil para conferir antes).
- **`DesenharTodasAsBarras`** — só (re)desenha as barras.
- **`LimparTodasAsBarras`** — remove as barras.

### Configurações no topo do módulo (`mdlRaioXP.bas`)
- `CONGELAR_HISTORICO` (padrão `True`) — cola o histórico em valores após puxar
  (deixa o arquivo rápido/portátil). Coloque `False` para manter as fórmulas BDH vivas.
- `TIMEOUT_SEG` (padrão `180`) — tempo máx. de espera do Bloomberg.

---

## Dados / Data
- Campo Bloomberg: **`BEST_PE_RATIO`** com `BEST_FPERIOD_OVERRIDE = "bf"` (blended forward 12m).
- Universo: índices setoriais **MSCI** — Brasil `MXBR`, Latam `MXLA`, EM `MXEF`, Mundo `MXWD`
  (total + 10 setores: Cons. Disc., Cons. Básico, Financeiro, Tecnologia, Energia,
  Indústria, Materiais, Utilities, Saúde, Telecom).
- Periodicidade mensal (`per=cm`), 121 pontos (10 anos), `Fill=P` (preenche vazios).
- Uma chamada `BDH` por índice (≈44 no total) — leve para o Terminal.

## Abas / Sheets
| Aba | Conteúdo |
|-----|----------|
| **Painel** | Data de fechamento, botão ATUALIZAR, instruções, carimbo. |
| **Consolidated / Consolidado (PT)** | P/E absoluto por setor nas 4 regiões (P/E, média 10a, mín, máx, barra). |
| **Relative / Relativo (PT)** | Brasil vs. Latam / EM / Mundo (P/E relativo, média 10a, mín, máx, barra). |
| **Data_BR / Data_LATAM / Data_EM / Data_World** | Engine BDH (histórico bruto + estatísticas). |
| **Calc_Rel** | Séries relativas (Brasil ÷ região) + estatísticas. |

> Observação: as fórmulas BDH só retornam dados **com o Terminal Bloomberg conectado**.
> Fora do Bloomberg, as células de dados aparecem vazias/#N/A até você rodar a macro no Terminal.
