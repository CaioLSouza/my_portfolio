// =============================================================================
// Query: RawData_Filtrada  (VARIANTE COM PARAMETROS — imune ao Formula.Firewall)
//
// Use esta versao se a original der o erro:
//   "Formula.Firewall: a consulta ... referencia outras consultas ou etapas,
//    portanto nao pode acessar diretamente uma fonte de dados"
// e voce nao quiser/puder marcar "Ignorar niveis de privacidade" nas opcoes.
//
// Em vez da tabela Config na planilha, os parametros vivem no proprio
// Power Query (parametros sao constantes para a engine -> sem firewall).
//
// Setup (1x):
//  1. Dados > Obter Dados > Iniciar Editor do Power Query
//  2. Pagina Inicial > Gerenciar Parametros > Novo:
//       Nome: CaminhoMestre   | Tipo: Texto  | Valor: C:\...\PA_Base_Historica.xlsm
//       Nome: MesesHistorico  | Tipo: Numero | Valor: 24
//  3. Nova consulta em branco > Editor Avancado > cole este codigo
//     > renomeie para RawData_Filtrada
//  4. Fechar e Carregar Para... > Planilha existente: 'Raw Data'!$A$1
//
// Para mudar caminho/meses depois: Dados > Obter Dados > Iniciar Editor
// > Gerenciar Parametros (nao e mais na planilha).
// =============================================================================
let
    // ---- abrir a mestre (CaminhoMestre e MesesHistorico sao PARAMETROS) ----
    Mestre  = Excel.Workbook(File.Contents(CaminhoMestre), null, true),
    RawWide = Table.PromoteHeaders(
                Mestre{[Item="Raw Data", Kind="Sheet"]}[Data],
                [PromoteAllScalars=true]),

    // ---- filtro de periodo: ultimos N meses (coluna "Survey" = AAAAMM) ----
    Periodos      = List.Sort(
                      List.Distinct(List.RemoveNulls(Table.Column(RawWide, "Survey"))),
                      Order.Descending),
    PeriodosManter = List.FirstN(Periodos, MesesHistorico),
    Filtrado      = Table.SelectRows(RawWide, each List.Contains(PeriodosManter, [Survey])),

    // ---- filtro de colunas: metadados + perguntas ativas do catalogo ----
    Catalogo = Table.PromoteHeaders(
                 Mestre{[Item="Perguntas", Kind="Sheet"]}[Data],
                 [PromoteAllScalars=true]),
    Ativas   = Table.Column(
                 Table.SelectRows(Catalogo, each [ativa] = 1),
                 "pergunta"),
    Meta     = List.FirstN(Table.ColumnNames(Filtrado), 5),  // Survey..Nome
    Manter   = Meta & List.Select(
                 Table.ColumnNames(Filtrado),
                 each List.Contains(Ativas, _) and not List.Contains(Meta, _)),
    Final    = Table.SelectColumns(Filtrado, Manter, MissingField.Ignore)
in
    Final
