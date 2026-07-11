# Pesquisa XP — Arquitetura em 2 camadas (mestre + produção)

Resolve a divergência: **base proprietária com histórico completo** vs.
**planilha leve para montar o relatório**.

```
┌─────────────────────────────┐      Power Query       ┌──────────────────────────┐
│  PA_Base_Historica.xlsm     │  (perguntas ativas ×   │  PA_Principal (produção) │
│  MESTRE · append-only       │ ────  N meses  ──────► │  enxuta · gera relatório │
│                             │                        │                          │
│  · Raw Data (larga/canônica)│                        │  · Raw Data = resultado  │
│  · Respostas (long)         │                        │    do Power Query        │
│  · Perguntas (catálogo+ativa)│                       │  · Base (motor COUNTIFS) │
│  ◄── ImportarForms (macro)  │                        │  · Charts (304 gráficos) │
└─────────────────────────────┘                        │  ◄── AtualizarProducao   │
        ▲                                              └──────────────────────────┘
   export .xlsx
   do MS Forms
```

## Arquivos
| Arquivo | Onde usar |
|---|---|
| `migrar_base.py` | Gera a `PA_Base_Historica.xlsx` a partir da sua `PA_Principal.xlsx` (1x) |
| `mdlBaseMestre.bas` | Importar **na mestre** (Alt+F11 → Import) e salvar como `.xlsm` |
| `mdlProducao.bas` | Importar **na produção** e salvar como `.xlsm` |
| `PowerQuery_RawDataFiltrada.m` | Colar no Power Query da produção (setup 1x, ver abaixo) |

> A base mestre com os dados **não está neste repositório** (repo público;
> os dados da pesquisa são proprietários). Gere localmente:
> `python3 migrar_base.py PA_Principal.xlsx -o PA_Base_Historica.xlsx`
> (requer `pip install openpyxl`)

## Setup — uma vez só

### Mestre
1. Rode a migração (comando acima), abra a `PA_Base_Historica.xlsx`, importe
   `mdlBaseMestre.bas`, salve como `.xlsm`.
2. Guarde num caminho estável (OneDrive/SharePoint/rede). O caminho é a "chave" do elo.

### Produção (a partir da sua PA_Principal atual)
1. Salve uma cópia da PA_Principal como `PA_Producao.xlsm` (backup antes!).
2. Crie uma aba `Config` com uma tabela nomeada **Config** (Inserir → Tabela) com
   colunas `CaminhoMestre` e `MesesHistorico` e 1 linha:
   `C:\...\PA_Base_Historica.xlsm` | `24`
3. **Limpe todo o conteúdo da aba `Raw Data`**.
4. Dados → Obter Dados → De Outras Fontes → **Consulta em Branco** → Editor
   Avançado → cole o conteúdo de `PowerQuery_RawDataFiltrada.m` → renomeie a
   consulta para `RawData_Filtrada` → Fechar e Carregar **Para...** →
   **Planilha existente**: `'Raw Data'!$A$1`.
5. Importe `mdlProducao.bas`.
6. Rode `AtualizarProducao` e confira se os números da edição atual batem
   com a versão antiga (mesma Base, mesmos gráficos).

> Os `COUNTIFS` da Base continuam funcionando sem alteração: eles casam a
> pergunta pelo texto do cabeçalho (`MATCH` na linha 1 do Raw Data) e o Power
> Query preserva os cabeçalhos exatos. Os 304 gráficos não são tocados.
> As colunas antigas da Base (valores colados) continuam lá — são elas que
> alimentam os gráficos de série histórica.

## Fluxo mensal (2 cliques)
1. **Mestre** → `ImportarForms` (Alt+F8): escolhe o export do Forms, informa o
   período. A macro anexa na larga + long e atualiza o catálogo.
2. **Produção** → `AtualizarProducao`: refresh do Power Query, cria a coluna da
   edição na Base, aponta os Charts pro mês novo e gera o log de alternativas
   novas na aba `_Log Atualizacao`.

## Governança das perguntas
- **Aposentar pergunta**: na mestre, aba `Perguntas`, coluna `ativa` → `0`.
  No próximo refresh ela some da produção; o histórico fica intacto na mestre.
- **Pergunta nova**: entra sozinha (catálogo com `ativa=1`) via `ImportarForms`;
  você só cria o bloco correspondente na Base da produção (o log avisa).
- **Consultas históricas** ("como evoluiu X em 2022?"): use a aba `Respostas`
  (long) da mestre — filtra por pergunta e período, e uma tabela dinâmica resolve.

## Limitações conhecidas
- O Power Query lê a mestre **fechada** pelo caminho da `Config`; se mover o
  arquivo, atualize o caminho.
- Textos de pergunta são a chave do elo (texto **exato**, incluindo espaços
  não-quebráveis). Se o texto mudar no Forms, vira "pergunta nova" — o log
  avisa e você decide (padronize no Forms ou unifique depois na mestre).
  Mudanças reais de redação **não** são fundidas automaticamente, de propósito:
  perguntas 98% similares podem ser legitimamente distintas (ex.: "Ibovespa ao
  fim de 2025" vs. "...2026").
- Macros não foram testadas contra um Forms real neste ambiente — rode a
  primeira vez em cópias.
