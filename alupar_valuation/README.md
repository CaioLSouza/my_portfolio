# Alupar (ALUP11) — modelo de valuation

DCF do fluxo de caixa ao acionista da Alupar, montado em **termos reais** e inteiramente dirigido
por fórmulas. A escolha por moeda constante não é estética: a RAP da transmissão é corrigida por
IPCA, então projetar em real e descontar a uma taxa real evita embutir inflação duas vezes — e
deixa a TIR resultante diretamente comparável com a NTN-B.

## Arquivos

| Arquivo | O que é |
|---|---|
| `alupar_valuation_model.xlsx` | **Comece aqui.** O modelo. 8 abas, 2.987 fórmulas, nenhum número calculado gravado como valor. |
| `build_alupar_model.py` | Gera o workbook do zero. Rodar de novo reconstrói o arquivo inteiro. |
| `requirements.txt` | Só `openpyxl`. |

```bash
pip install -r requirements.txt
python build_alupar_model.py
```

## Abas

| Aba | Conteúdo |
|---|---|
| `Read me` | Metodologia, código de cores, limitações |
| `Inputs` | Todas as premissas editáveis (amarelo), agrupadas por bloco |
| `Dados de origem` | Os números públicos coletados, cada um com a sua fonte |
| `Transmissão` | RAP real ano a ano, base operacional e pipeline, 2026–2080 (+ gráfico) |
| `Geração` | Energia assegurada contratada e comercializadora |
| `Consolidado` | FCFE, rolagem de dívida e a **aferição contra o divulgado** |
| `Valuation` | DCF, preço-alvo, TIR real implícita, abertura por segmento |
| `Sensibilidade` | Preço-alvo e upside por Ke × choque no fluxo; TIR por preço de entrada |

Editar qualquer célula amarela recalcula tudo, inclusive as sensibilidades — elas são fórmulas
fechadas, não tabelas de dados do Excel, então aparecem corretas em qualquer leitor de planilha.

## Como a transmissão é construída

A RAP bruta da base operacional é **reconstruída** a partir da receita líquida regulatória de
transmissão do 1T26 anualizada, revertida pela alíquota de deduções — a RAP consolidada da
companhia não estava disponível publicamente na coleta.

O pipeline é tratado por safras. O capex de R$ 9,1 bi é distribuído entre 2026 e 2029, mais um
capex recorrente para os leilões seguintes, e cada safra gera RAP a partir de dois anos depois do
desembolso, por 30 anos. O horizonte vai até 2080 justamente para que a última safra complete sua
concessão dentro do modelo: assim o valor terminal é zero de verdade, e não uma perpetuidade
escondendo o resultado.

A RAP por real investido sai do último leilão (Lote 7: RAP de R$ 96,7 mn sobre capex de referência
de R$ 1.089 mn = 8,9%), corrigida por um fator de eficiência de construção — construir abaixo da
referência da ANEEL é de onde vem boa parte do retorno em transmissão.

## Aferição

O modelo é conferido contra três âncoras divulgadas, na parte de baixo da aba `Consolidado`:

| Aferição | Modelo | Divulgado | Desvio |
|---|---:|---:|---:|
| EBITDA consolidado 2026 | R$ 3.069 mn | R$ 3.180 mn (1T26 × 4) | −3,5% |
| Receita de geração + comercialização | R$ 1.032 mn | R$ 1.031 mn (implícita no 1T26) | +0,1% |
| Pico de alavancagem | 3,5x em 2027 | 3,9–4,0x em 2028 (guidance) | −0,45x |

O workbook foi recalculado de ponta a ponta e não tem nenhuma célula de erro. Isso atesta a
aritmética, não as premissas.

## O que esta reconstrução corrigiu

A branch anterior tinha os dados de mercado desatualizados. Três premissas foram substituídas por
dados verificados de fontes públicas em 31-jul-2026 (ver `Dados de origem` e as notas de cada input
em `Inputs`):

| Input | Antes | Agora | Fonte |
|---|---:|---:|---|
| NTN-B 10 anos (juro real) | 7,00% | **8,33%** | Tesouro IPCA+ 2035, fechamento 31-jul-2026 |
| Cotação ALUP11 | R$ 33,75 (15-jul-2026) | **R$ 32,62** (31-jul-2026) | Status Invest / Dados de Mercado |
| Eficiência de capex do Lote 7 vs. referência ANEEL | 80% (20% de economia, estimado) | **70%** (~30% de economia, noticiado) | ADVFN, jul/2026 |
| Início/fim dos vencimentos de concessão | 2042–2055 (intervalo estimado) | **2030–2047** (3 concessões reais: ECTE, EBTE, Aimorés) | Imprensa setorial |

O resto da base pública (ações em circulação, patrimônio líquido, receita e EBITDA do 1T26, dívida
líquida, sistemas de transmissão, RAP e capex do último leilão, capacidade instalada de geração)
foi conferido de forma independente contra Status Invest, Investidor10, InfoMoney, CNN Brasil e a
própria ANEEL e bateu com o que já estava na aba `Dados de origem` — não precisou de correção.

**A NTN-B desatualizada é a que mais pesou.** Sozinha, ela derruba o Ke real de 11,5% para 12,83% —
e como o fluxo roda até 2080, 133 pontos-base a mais de desconto compostos por décadas pesam mais
que qualquer premissa operacional. O preço-alvo cai de ~R$ 21 para **R$ 11,62/unit**.

**A alíquota efetiva domina o lado operacional.** A primeira versão usava 20% do EBITDA, que
parecia prudente. Com ela o preço-alvo caía ~40% e, pior, cada real de capex novo passava a
destruir valor: aumentar o programa de investimentos *reduzia* o preço-alvo. Isso não descreve uma
companhia que compõe valor arrematando lote atrás de lote há décadas — era sinal de erro, não de
conservadorismo. As SPEs de transmissão apuram em lucro presumido (imposto ≈ 3–4% da receita
bruta) e boa parte do portfólio tem redução de IR por SUDAM/SUDENE, o que põe a carga efetiva na
casa de 5–10% do EBITDA. Se você mexer neste input, confira sempre se a expansão continua criando
valor — é o melhor teste de sanidade do arquivo.

**O modelo não reproduz o preço de mercado, e não se deve forçá-lo a isso — e com a NTN-B corrigida
o gap ficou maior, não menor.** Com as premissas atuais o DCF dá R$ 11,62/unit contra R$ 32,62 de
cotação (31-jul-2026), um gap de ~R$ 21/unit — o dobro do que era antes da correção da taxa. Mais
revelador: a TIR real implícita no preço atual caiu para **4,75% a.a., abaixo dos 8,33% da própria
NTN-B**. Pelo fluxo deste modelo, quem compra ALUP11 hoje aceita um retorno real menor que o do
título público que deveria ser seu piso. As linhas "Gap a explicar" na aba `Valuation` medem essa
diferença. Ela é a pergunta de investimento, não um defeito a calibrar: o mercado está pagando por
renovação de concessões, leilões além de 2045, sinergias, ou usando um custo de capital menor que
os 12,83% reais assumidos aqui — ou o modelo ainda está pessimista demais na base operacional.
**A leitura mais robusta do arquivo é a TIR real implícita, não o preço-alvo** — ela não depende de
escolher um Ke.

## Limitações que importam

- **O cronograma de vencimentos ainda é uma média, agora ancorada em datas reais.** A base
  operacional são 31 sistemas com datas de outorga distintas, e a lista completa não está
  disponível publicamente. O decaimento linear entre 2030 e 2047 usa as três únicas concessões da
  Alupar com data publicada (ECTE 2030, EBTE 2038, Aimorés 2047) em vez de um intervalo inventado,
  mas ainda aplica a média de três pontos aos 31 ativos. É a premissa que mais move o valor no longo
  prazo — troque-a por um cronograma ativo a ativo assim que tiver a lista completa da ANEEL.
- **O pipeline é tratado em bloco.** Treze projetos com capex, RAP e datas próprias viram um
  agregado ao yield do último leilão.
- **A geração é premissa, não dado.** MW médio, preço e opex foram calibrados para reproduzir a
  receita implícita no trimestre, não extraídos dos PPAs.
- **Os dados de origem vêm de agregadores e da imprensa**, não dos arquivos da companhia — o acesso
  direto ao site de RI e aos releases foi bloqueado pela rede na montagem. Confira a aba
  `Dados de origem` contra o release oficial antes de usar isto para qualquer coisa que importe.

## Uso

Material de estudo. Não é recomendação de investimento, e os números não foram auditados contra as
demonstrações financeiras da companhia.
