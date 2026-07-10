# Pessoa física na Bolsa (B3)

Coleta, direto da B3, o **número total de contas de pessoa física** e a
**posição total (R$)** e acrescenta o valor no fim das duas planilhas
históricas usadas no relatório de *Fluxo de investidores na Bolsa*.

Fonte: **Perfil de pessoas físicas → Faixa etária**
<https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/perfil-pessoas-fisicas/faixa-etaria/>

## Por que Selenium

Essa página da B3 é um app Angular: os números **não vêm no HTML** servido, são
carregados por uma chamada interna de API e montados no navegador. Por isso a
coleta abre a página num Chrome automatizado (Selenium), espera a tabela
renderizar e lê os totais do DOM já pronto — em vez de um `requests.get`, que
traria só a casca da página.

## Instalação

```bash
pip install -r requirements.txt
```

Requisitos: **Python 3.10+** e **Google Chrome** instalado. O `chromedriver` é
baixado/gerenciado automaticamente pelo Selenium (Selenium Manager) — não
precisa instalar nada à mão. (Em rede corporativa que bloqueie esse download,
aponte a variável `SE_CHROMEDRIVER` para um chromedriver local.)

## Uso

```bash
# Coleta e já grava nas duas planilhas (faz backup .bak antes):
python atualizar_planilhas.py

# Só confere o que faria, sem tocar nas planilhas:
python atualizar_planilhas.py --dry-run

# Acompanhar o navegador / diagnosticar quando algo não bater:
python atualizar_planilhas.py --no-headless --debug
```

As planilhas de destino (na rede da XP) já vêm como padrão:

| Arquivo            | Colunas          | Conteúdo gravado                    |
| ------------------ | ---------------- | ----------------------------------- |
| `PF na Bolsa.xlsx` | `data`, `Número` | nº de contas PF                     |
| `Posição PF.xlsx`  | `data`, `posição`| posição total em **R$ bilhões**     |

Troque com `--planilha-numero` / `--planilha-posicao` se os caminhos mudarem.

## Detalhes que importam

- **Data registrada.** Por padrão (`--data auto`) usa a data-base lida na
  própria página. Use `--data hoje` ou `--data dd/mm/aaaa` para forçar.
- **Unidade da posição.** A página traz o valor em reais; o script grava em
  **R$ bilhões** dividindo por `1e9` (`--fator-posicao`). Confira o número
  impresso (`Posição (valor bruto R$)` vs `Posição (R$ bilhões)`) e ajuste o
  divisor se a página passar a exibir o valor em outra unidade.
- **Idempotente.** Se a data já existir na planilha, a linha **não** é
  duplicada (só avisa). Use `--sobrescrever` para atualizar o valor daquela data.
- **Sempre roda um `--dry-run` primeiro** quando desconfiar do layout: o script
  imprime de onde tirou os totais (`linha de total` ou `soma das faixas`).

## Arquivos

| Arquivo                  | Papel                                                        |
| ------------------------ | ----------------------------------------------------------- |
| `scraper_b3_pf.py`       | abre a página (Selenium) e extrai os totais da tabela       |
| `planilhas.py`           | anexa `(data, valor)` no `.xlsx` preservando o formato       |
| `atualizar_planilhas.py` | CLI que junta coleta + escrita                              |
| `test_logica.py`         | testes da lógica pura (parsing e Excel), sem rede/navegador |

> Roda na máquina do analista (Windows, dentro da rede da XP) porque grava nos
> `.xlsx` do compartilhamento `\\xpdocs\...` e depende de um Chrome real — não é
> um job de GitHub Actions.
