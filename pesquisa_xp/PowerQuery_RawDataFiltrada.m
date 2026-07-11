// =============================================================================
// Query: RawData_Filtrada
// Carrega na planilha de PRODUCAO apenas o recorte necessario da base mestre:
//   - ultimos N meses  (parametro na tabela "Config" da producao)
//   - apenas perguntas com ativa=1 no catalogo "Perguntas" da mestre
//
// Setup (1x): Dados > Obter Dados > De Outras Fontes > Consulta em Branco
//   > Editor Avancado > colar este codigo > Fechar e Carregar Para...
//   > Planilha existente: 'Raw Data'!$A$1  (limpe a aba antes)
//
// Pre-requisito: na producao, criar uma tabela nomeada "Config" com colunas
//   CaminhoMestre | MesesHistorico   (ex.: C:\...\PA_Base_Historica.xlsm | 24)
// =============================================================================
let
    // ---- parametros da producao ----
    Cfg            = Excel.CurrentWorkbook(){[Name="Config"]}[Content],
    CaminhoMestre  = Text.Trim(Cfg{0}[CaminhoMestre]),
    MesesHistorico = Cfg{0}[MesesHistorico],

    // ---- abrir a mestre ----
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
