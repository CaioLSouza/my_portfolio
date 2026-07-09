# Lâmina de Carteiras — geração automática do PPT

Script que atualiza automaticamente uma lâmina em PowerPoint (ex. *Carteira
Top Ações XP*) a partir dos dados de uma planilha Excel, preservando toda a
formatação do template.

## O que é atualizado

O script usa **duas planilhas**: a de gráficos (`Charts Lâmina Carteiras.xlsm`)
e a de composição (`output/composicao_*.xlsx`, gerada à parte).

| Item | Origem |
|---|---|
| Gráfico de desempenho (base 100) | Referências de células gravadas no próprio gráfico (`Charts Base 100`) |
| Tabela de retornos mensais (Figura 1) | `performance_top_ações` / `performance_top_divs` / `performance_top_smll` |
| Tabela de desempenho por ativo (Figura 2) | `Desempenho ativo * _last` |
| Tabela de indicadores — Sharpe, Volatilidade, Beta (Figura 4) | `* Portfolio Metrics` |
| Tabela de composição (slide 1) — setores, pesos, rating, preço-alvo | `composicao_*.xlsx`, aba `PT` |
| Tabela de teses (slide 4) — peso, recomendação, preço-alvo, **link** | `composicao_*.xlsx`, aba `PT_data` |
| Datas dos slides ("2 de julho de 2026", "Julho 2026") | Parâmetro `--data` (padrão: hoje) |

**Continuam manuais** (conteúdo editorial que não existe em planilha): a
manchete, o comentário da carteira (slides 1 e 2) e o **texto** dos
comentários por tese na tabela do slide 4. Esses comentários são
**preservados** de um mês para o outro casando pelo ticker — só papéis novos
entram com o comentário em branco (o script avisa quais).

## Como funciona

* **Gráficos** — os gráficos do template foram copiados do Excel e guardam no
  XML as referências às células de origem (ex.
  `'Charts Base 100'!$M$4:$M$10000`). O script lê os valores atuais dessas
  células e substitui os dados de cada série via `python-pptx`, mantendo
  cores, eixos, legenda e o Excel embutido do "Editar Dados". Como os ranges
  vão até a linha 10000, novos meses entram sozinhos.
* **Tabelas** — cada tabela é identificada pelo cabeçalho (não pelo nome do
  shape), e as células são preenchidas preservando a formatação existente.
  A tabela de ativos **cresce ou encolhe** conforme o número de papéis na
  planilha (linhas são clonadas/removidas no XML). Os rótulos dos meses da
  tabela de retornos vêm da planilha, então a janela de 12 meses desliza
  automaticamente a cada atualização.
* **Tabela de composição** — a aba `PT` da planilha de composição já vem com
  as células de segmento/setor **em branco** onde há agrupamento; o script
  usa esse padrão de brancos para reconstruir as mesclagens verticais da
  tabela do slide 1. Ou seja, se o agrupamento de setores mudar no mês, os
  merges se reajustam sozinhos.
* **Tabela de teses** — preenche peso/recomendação/preço-alvo da composição e
  monta o link de cada papel como `https://conteudos.xpi.com.br/acoes/TICKER`.
  Antes de reconstruir, guarda os comentários por ticker e os recoloca, de
  modo que reordenar/adicionar/remover papéis não embaralha os comentários.
* **Datas** — os placeholders de data do template são campos automáticos do
  PowerPoint (`datetime4`), que se atualizam sozinhos ao abrir o arquivo; o
  script também grava o texto em cache para que exports (PDF, prévias)
  mostrem a data certa.

## Uso

```bash
pip install -r requirements.txt

# usa os caminhos padrão da rede (\\xpdocs\...\Carteiras de Ações XP)
python gerar_ppt.py
```

Os caminhos padrão (template, planilha e saída) estão definidos no topo do
`main()` em `gerar_ppt.py` (constantes `TEMPLATE_PADRAO`, `PLANILHA_PADRAO`
e `SAIDA_PADRAO`) e podem ser sobrescritos por argumento:

```bash
python gerar_ppt.py \
    --template   "Carteira Top Ações - Julho 2026.pptx" \
    --planilha   "Charts Lâmina Carteiras.xlsm" \
    --composicao "composicao_top_acoes.xlsx" \
    --saida      "Carteira Top Ações - Agosto 2026.pptx" \
    --carteira   top_acoes \
    --data       04/08/2026
```

`--carteira` aceita `top_acoes` (padrão), `top_div` e `top_smll` — o mesmo
script serve para as três lâminas, mudando apenas as abas de origem das
tabelas. `--data` é opcional (padrão: data de hoje).

### Em notebook / interactive window (VS Code, Jupyter)

Importe a função `gerar_lamina` e chame direto de uma célula:

```python
from gerar_ppt import gerar_lamina

gerar_lamina()                        # caminhos padrão da rede
gerar_lamina(data="04/08/2026")       # data específica
gerar_lamina(carteira="top_div",      # outra carteira, outros caminhos
             template=r"C:\lâminas\Carteira Top Dividendos.pptx",
             saida=r"C:\lâminas\Top Dividendos XP.pptx")
```

Rodar o arquivo inteiro na interactive window também funciona: o `main()`
usa `parse_known_args`, que ignora os argumentos extras injetados pelo
kernel do Jupyter (ex. `--f=kernel.json`).

`--composicao` é opcional (padrão: `output/composicao_<carteira>.xlsx`). Se o
arquivo não existir, as tabelas de composição e teses são mantidas como no
template e o resto roda normalmente.

Saída esperada:

```
Lendo planilha: Charts Lâmina Carteiras.xlsm
Lendo composição: ...\output\composicao_top_acoes.xlsx
Lendo template: Carteira Top Ações.pptx
  [slide 1 / Table 1] composição atualizada: 16 papel(is)
  [slide 3 / Table 36] indicadores atualizados: 3 linha(s)
  [slide 3 / Table 2] retornos atualizados: 2 série(s), 12 mês(es) até jun-26
  [slide 3 / Table 6] desempenho por ativo atualizado: 16 papel(is)
  [slide 3 / Chart 9] gráfico atualizado: 2 série(s), 331 ponto(s) (2025-02-28 a 2026-06-30)
  [slide 4 / Table 21] teses atualizadas: 16 papel(is), links por ticker
  datas atualizadas para '4 de agosto de 2026' (6 ocorrência(s))
OK: 6 objeto(s) atualizado(s) -> Carteira Top Ações.pptx
```

## Fluxo mensal sugerido

1. Atualizar a planilha `Charts Lâmina Carteiras.xlsm` no Excel e **salvar**
   (o script lê os valores calculados que o Excel grava no arquivo); garantir
   que o `output/composicao_<carteira>.xlsx` do mês foi gerado;
2. Rodar o script (`python gerar_ppt.py`);
3. Ajustar à mão só a manchete, o comentário da carteira e o texto dos
   comentários por tese dos **papéis novos** (o script lista quais faltam).

## Limitações e observações

* As planilhas precisam ter sido salvas pelo Excel — o script lê os valores
  calculados em cache das fórmulas (`data_only=True` do openpyxl).
* A tabela de desempenho por ativo usa as abas `*_last` (composição vigente
  no período reportado), reproduzindo o comportamento do template original.
* As mesclagens da tabela de composição são reconstruídas a partir do padrão
  de células em branco da aba `PT` — mantenha essa aba com os brancos de
  agrupamento (é como o gerador da composição já a entrega).
* Se um gráfico ou tabela referenciar uma aba inexistente, o script falha
  com erro claro indicando a aba/arquivo faltante.
