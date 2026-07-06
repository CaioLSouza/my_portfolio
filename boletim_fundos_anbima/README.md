# Boletim de Fundos de Investimento (ANBIMA/CVM)

Download recorrente dos dados diarios de fundos de investimento (ICVM 555) que
sustentam as estatisticas do [Boletim de Fundos de Investimento da ANBIMA](https://www.anbima.com.br/pt_br/informar/relatorios/fundos-de-investimento/boletim-de-fundos-de-investimentos/boletim-de-fundos-de-investimentos.htm):
patrimonio liquido, captacao/resgate, numero de cotistas e valor de cota, por fundo.

## Por que a fonte e a CVM e nao a ANBIMA diretamente?

O boletim da ANBIMA em si e um relatorio mensal (texto + graficos), sem download
automatizavel. Os dados brutos por tras dele so estao disponiveis via
**ANBIMA Feed**, uma API OAuth2 paga que exige cadastro (`client_id`/`client_secret`)
em https://developers.anbima.com.br.

O [Portal de Dados Abertos da CVM](https://dados.cvm.gov.br) publica a mesma
informacao regulatoria (Informe Diario de Fundos ICVM 555) de forma **gratuita,
sem cadastro**, atualizada de segunda a sabado as 08h. E a fonte usada neste
script. Se no futuro voce tiver credenciais da ANBIMA Feed, o mesmo padrao de
script pode ser adaptado trocando a chamada HTTP pela API oficial.

## Uso manual

```bash
pip install -r requirements.txt
python download_fundos.py                    # mes/ano corrente
python download_fundos.py --ano 2026 --mes 6  # mes especifico
```

Por padrao baixa todos os ~16 mil fundos regulados pela ICVM 555. Para
acompanhar apenas fundos especificos, liste os CNPJs (um por linha) em
`fundos_acompanhados.txt`, ou passe via `--cnpjs`.

Os arquivos sao salvos em `data/informe_diario_fi_{ano}{mes}.csv`.

## Download recorrente automatico

O workflow `.github/workflows/download-fundos-anbima.yml` roda todos os dias
(a CVM atualiza o mes corrente diariamente com eventuais retificacoes),
baixa o informe do mes vigente e faz commit dos dados atualizados no
repositorio automaticamente.

Para rodar manualmente: aba **Actions** do GitHub > "Download dados de fundos
ANBIMA/CVM" > **Run workflow**.
