# Tracker de teleconferências de resultados

Lê as transcrições das teleconferências de resultados das empresas cobertas e
transforma texto em dado: **tom da gestão**, **temas discutidos** (com
sentimento e intensidade), **mudanças de guidance** e **perguntas em que a
gestão desviou**, trimestre a trimestre. Com isso dá para responder, por
exemplo:

- "O varejo falou menos de inadimplência neste trimestre do que no anterior?"
- "Quais empresas ficaram mais cautelosas em relação ao trimestre anterior?"
- "Quem revisou guidance para baixo, e de quê?"
- "Em que temas as gestões mais fugiram das perguntas?"

A extração é feita pelo Claude (API da Anthropic) com **saída estruturada**:
o modelo devolve um JSON que segue o esquema em `esquema.py`, validado pelo
SDK. A agregação e o relatório são código determinístico (pandas), sem LLM,
então os números podem ser auditados.

## Fluxo

```
transcricoes/<TICKER>/<ANO>T<TRI>.pdf   ──extrair.py──▶   extracoes/<TICKER>_<PERIODO>.json
                                                                     │
                                                                agregar.py
                                                                     ▼
                              resultados/painel_empresas.csv, temas.csv,
                              temas_por_setor.csv, relatorio_<PERIODO>.md
```

| Arquivo | O que faz |
|---|---|
| `esquema.py` | Esquema da extração: tom (-2 a +2), temas de uma **taxonomia fechada** (para dar para comparar entre empresas e trimestres), guidance e perguntas do Q&A. |
| `extrair.py` | Lê cada transcrição (PDF ou TXT), chama o Claude e salva o JSON. Pula o que já foi processado, então pode rodar a cada temporada de resultados. **Confere cada citação contra o texto original** e lista as que não encontrar, para revisão. |
| `agregar.py` | Consolida os JSONs em tabelas (formato longo, prontas para Excel ou Power BI) e gera o rascunho do relatório do trimestre. |
| `empresas.csv` | Ticker → nome e setor. **Troque pelo setor XPQS** (`sector_xp`) para ficar no mesmo padrão das carteiras. |

## Como usar

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # ou `ant auth login`

# 1. Coloque as transcrições em transcricoes/<TICKER>/<ANO>T<TRI>.pdf
#    ex.: transcricoes/ITUB4/2025T2.pdf
python extrair.py --listar          # confere o que vai ser processado
python extrair.py                   # extrai (só o que é novo)

# 2. Tabelas e relatório
python agregar.py                   # trimestre mais recente
python agregar.py --periodo 2025T2
```

Testes (offline, sem chamar a API): `python -m pytest tests`.

### De onde vêm as transcrições

A maior parte das empresas da B3 publica a transcrição (ou o áudio) da
teleconferência na central de resultados do site de RI. Para o protótipo,
baixe manualmente as de 10 a 20 empresas em 2 ou 3 trimestres: é o mínimo
para as comparações entre trimestres fazerem sentido. Transcrições em inglês
funcionam normalmente (as citações ficam no idioma original e o resto sai em
português).

As transcrições não são versionadas (`.gitignore`). As extrações e os
resultados, sim.

## Custo

Uma teleconferência tem entre 10 mil e 25 mil palavras, algo como 15 mil a
40 mil tokens de entrada. Com o modelo padrão (`claude-opus-5`), fica na
ordem de US$ 0,10 a 0,40 por teleconferência, incluindo a resposta: algo como
US$ 10 a 40 para cobrir 100 empresas num trimestre. Para trocar de modelo,
use a variável `TRACKER_MODELO`. Se o volume crescer, a Batch API da
Anthropic custa 50% menos e cabe bem aqui, porque nada é urgente.

## Limitações e cuidados

- **Tom é uma leitura, não um fato.** Use-o para comparar ao longo do tempo e
  entre pares (a mesma régua para todos), não como nota absoluta. Vale
  calibrar lendo manualmente uma amostra e ajustando o `SYSTEM_PROMPT` em
  `extrair.py`.
- **Revisão humana antes de uso externo.** O relatório é rascunho. As
  citações não encontradas na transcrição ficam sinalizadas no JSON e no
  relatório.
- **Taxonomia fixa.** Se um tema começar a aparecer muito em "outros",
  promova-o a tema próprio em `esquema.py` e reprocesse com `--forcar`.
- **Compliance.** Só entra dado público (transcrições de RI). Um produto
  publicado a partir daqui segue as regras normais de research (CVM
  Resolução 20): a IA estrutura o que a empresa disse, e a opinião continua
  sendo do analista.

## Próximos passos

1. Rodar num trimestre real com 10 a 20 empresas e calibrar o prompt.
2. Cruzar o tom e os temas com o retorno da ação depois da divulgação (base
   Economatica), para ver se o sinal tem valor.
3. Automatizar a coleta nos sites de RI e a transcrição de áudio, quando só
   houver áudio.
4. Montar um painel (Power BI ou Streamlit, no molde do
   `xp-strategy-dashboard`) com a evolução por setor e tema.
