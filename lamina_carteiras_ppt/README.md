# Lâmina de Carteiras — geração automática do PPT

Script que atualiza automaticamente os gráficos de uma lâmina em PowerPoint
(ex. *Carteira Top Ações XP*) a partir dos dados de uma planilha Excel,
preservando toda a formatação do template.

## Como funciona

Os gráficos do template PPT foram originalmente copiados do Excel e, por isso,
guardam no XML interno as referências às células de origem — por exemplo
`'Charts Base 100'!$M$4:$M$10000`. O script:

1. Abre o template `.pptx` e localiza todos os gráficos nativos;
2. Lê as referências de cada série (categorias, valores e nome) e busca os
   valores atuais na planilha `.xlsm` (usa os valores calculados salvos pelo
   Excel — salve a planilha no Excel antes de rodar);
3. Substitui os dados de cada gráfico via `python-pptx`, mantendo cores,
   eixos, legenda e layout do template (inclusive o Excel embutido usado
   pelo "Editar Dados" do PowerPoint);
4. Salva o novo `.pptx`.

Como as referências apontam para ranges largos (até a linha 10000), novos
meses de dados entram automaticamente: basta atualizar a planilha e rodar o
script de novo — não é preciso mexer no template.

## Uso

```bash
pip install -r requirements.txt

python gerar_ppt.py \
    --template "Carteira Top Ações - Julho 2026.pptx" \
    --planilha "Charts Lâmina Carteiras.xlsm" \
    --saida    "Carteira Top Ações - Agosto 2026.pptx"
```

Saída esperada:

```
Lendo planilha: Charts Lâmina Carteiras.xlsm
Lendo template: Carteira Top Ações - Julho 2026.pptx
  [slide 3 / Chart 9] atualizado: 2 série(s), 331 ponto(s) (2025-02-28 a 2026-06-30)
OK: 1 gráfico(s) atualizado(s) -> Carteira Top Ações - Agosto 2026.pptx
```

## Limitações e observações

* Apenas **gráficos nativos** do PowerPoint são atualizados. Textos (datas,
  títulos, comentários) e tabelas do template precisam ser editados à parte.
* O script exige que a planilha tenha sido salva pelo Excel, pois lê os
  valores em cache das fórmulas (`data_only=True` do openpyxl). Uma planilha
  gerada só por script, sem passar pelo Excel, teria fórmulas sem valor.
* Se um gráfico do template referenciar uma aba que não existe na planilha,
  o script falha com erro claro indicando a aba faltante.
