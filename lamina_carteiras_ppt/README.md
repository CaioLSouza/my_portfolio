# Lâmina de Carteiras — geração automática do PPT

Script que atualiza automaticamente uma lâmina em PowerPoint (ex. *Carteira
Top Ações XP*) a partir dos dados de uma planilha Excel, preservando toda a
formatação do template.

## O que é atualizado

| Item | Origem na planilha |
|---|---|
| Gráfico de desempenho (base 100) | Referências de células gravadas no próprio gráfico (`Charts Base 100`) |
| Tabela de retornos mensais (Figura 1) | `performance_top_ações` / `performance_top_divs` / `performance_top_smll` |
| Tabela de desempenho por ativo (Figura 2) | `Desempenho ativo * _last` |
| Tabela de indicadores — Sharpe, Volatilidade, Beta (Figura 4) | `* Portfolio Metrics` |
| Datas dos slides ("2 de julho de 2026", "Julho 2026") | Parâmetro `--data` (padrão: hoje) |

As tabelas **editoriais** (composição da carteira com rating/preço-alvo e a
tabela de comentários por papel) não existem na planilha e continuam sendo
editadas à mão — o script as detecta e não mexe nelas.

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
    --template "Carteira Top Ações - Julho 2026.pptx" \
    --planilha "Charts Lâmina Carteiras.xlsm" \
    --saida    "Carteira Top Ações - Agosto 2026.pptx" \
    --carteira top_acoes \
    --data     04/08/2026
```

`--carteira` aceita `top_acoes` (padrão), `top_div` e `top_smll` — o mesmo
script serve para as três lâminas, mudando apenas as abas de origem das
tabelas. `--data` é opcional (padrão: data de hoje).

Saída esperada:

```
Lendo planilha: Charts Lâmina Carteiras.xlsm
Lendo template: Carteira Top Ações - Julho 2026.pptx
  [slide 1 / Table 1] tabela editorial — mantida como está
  [slide 3 / Table 36] indicadores atualizados: 3 linha(s)
  [slide 3 / Table 2] retornos atualizados: 2 série(s), 12 mês(es) até jun-26
  [slide 3 / Table 6] desempenho por ativo atualizado: 16 papel(is)
  [slide 3 / Chart 9] gráfico atualizado: 2 série(s), 331 ponto(s) (2025-02-28 a 2026-06-30)
  [slide 4 / Table 21] tabela editorial — mantida como está
  datas atualizadas para '4 de agosto de 2026' (6 ocorrência(s))
OK: 4 objeto(s) atualizado(s) -> Carteira Top Ações - Agosto 2026.pptx
```

## Fluxo mensal sugerido

1. Atualizar a planilha `Charts Lâmina Carteiras.xlsm` no Excel e **salvar**
   (o script lê os valores calculados que o Excel grava no arquivo);
2. Rodar o script apontando para o template do mês anterior;
3. Ajustar à mão apenas o conteúdo editorial: título/manchete, comentário da
   carteira, tabela de composição (rating, preço-alvo) e comentários por papel.

## Limitações e observações

* A planilha precisa ter sido salva pelo Excel — uma planilha gerada só por
  script, sem passar pelo Excel, teria fórmulas sem valor em cache
  (`data_only=True` do openpyxl).
* A tabela de desempenho por ativo usa as abas `*_last` (composição vigente
  no período reportado), reproduzindo o comportamento do template original.
* Se um gráfico ou tabela referenciar uma aba inexistente, o script falha
  com erro claro indicando a aba faltante.
