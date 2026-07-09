# Prestação de Contas — preenchimento automático do PPT

Preenche o PowerPoint mensal de **Prestação de Contas** das carteiras a partir
dos dados já calculados pelo pipeline `portfolio_automation.py`, preservando
toda a formatação do template.

Este módulo (`atualizar_prestacao.py`) é **auto-contido**: recebe os dados como
DataFrames e não acessa rede nem segredos. Ele é chamado pelo pipeline, que
calcula os insumos.

## O que é atualizado no template

| Elemento (slide) | Origem |
|---|---|
| Tabela "Desempenho" 3×4 (mês de ref. / acumulado no ano / 12 meses) | `df_port` (base 100) |
| Gráfico de linha base 100 (carteira vs. benchmark) | `df_port` |
| Gráfico **waterfall** — decomposição do retorno por papel (barra final = retorno da carteira) | `df_dec` (`decomposicao_retorno`) |
| Tabela de composição (Setor \| Companhia \| Ticker \| Peso) | `df_comp` (`montar_df_composicao_compacta`) |
| Datas dos slides (mês de referência e mês da carteira) | parâmetros `ano_ref`/`mes_ref` |

**Continuam manuais** (conteúdo editorial): os comentários do analista e o
texto de "Alterações na Carteira".

## Como funciona

* **Tabela de desempenho** — identificada pelo cabeçalho ("Desempenho");
  preenche mês/ano/12m para a carteira e o benchmark, casando as linhas pelo
  rótulo (robusto a Small Caps, que usa SMLL no lugar do Ibovespa).
* **Composição** — a coluna Setor é **mesclada por grupo**: setores iguais
  consecutivos viram uma célula mesclada; a tabela cresce/encolhe conforme o
  número de papéis.
* **Gráfico de decomposição (waterfall)** — o template traz esse gráfico de
  colunas vazio (e apontando para uma fonte externa), então o `replace_data`
  do python-pptx não funciona. Como o python-pptx também não escreve
  waterfall nativo, o módulo monta o waterfall com **colunas empilhadas**:
  uma série "base" invisível flutua cada barra até o acumulado, séries de
  alta (verde) e baixa (vermelho) desenham a variação de cada papel, e a
  última barra (azul) é o retorno total da carteira. Para a base não cruzar
  o zero, as contribuições são ordenadas de modo que o caminho acumulado
  fique sempre do mesmo lado (positivas primeiro em mês de alta; negativas
  primeiro em mês de baixa).
* **Gráfico de linha** — usa `replace_data`, preservando estilo e os nomes
  originais das séries.
* **Datas** — mês de referência = mês fechado; mês da carteira = referência +
  1. Os textos são trocados por shape (identificados por nome no template).

## Como plugar no pipeline

No `portfolio_automation.py`, depois de calcular `df_port`, `composition` etc.,
basta:

```python
from atualizar_prestacao import atualizar_prestacao_contas
from portfolio_automation import (           # funções já existentes no pipeline
    montar_df_composicao_compacta, decomposicao_retorno, _df_para_lamina,
)

portfolio = 'Carteira - TOP Ações XP'
df_port = _df_para_lamina(portfolio)
comp    = composition_dict[portfolio]

# mês de referência (fechado); a composição/alterações são do mês seguinte
ano_ref, mes_ref = 2026, 6

atualizar_prestacao_contas(
    caminho_template=r"...\Templates\Prestação de Contas - Top Ações.pptx",
    caminho_saida=r"...\Prestação de Contas\Prestação de Contas - Top Ações.pptx",
    df_port=df_port,
    df_comp=montar_df_composicao_compacta(comp, idioma='PT'),
    df_dec=decomposicao_retorno(comp, ano_ref, mes_ref),
    ano_ref=ano_ref, mes_ref=mes_ref,
)
```

> A versão integrada ao `portfolio_automation.py` (Seção 17) já faz tudo isso
> num laço por carteira, com `prestacao_config` (template/saída por carteira) —
> peça o arquivo integrado se preferir rodar direto do pipeline.

## Teste

`teste_sintetico.py` preenche o template com dados de exemplo (sem rede), para
validar o mapeamento:

```bash
pip install -r requirements.txt
python teste_sintetico.py "Prestação de Contas - Top Ações.pptx" saida.pptx
```

## Observações

* O gráfico de decomposição exibe os valores em cache; o "Editar Dados" no
  PowerPoint ainda aponta para a fonte externa original do template (que não
  é usada). O visual fica correto.
* O mês de referência padrão (quando `ano_ref`/`mes_ref` não são passados) é o
  mês da última data de `df_port`. Passe explicitamente para garantir.
