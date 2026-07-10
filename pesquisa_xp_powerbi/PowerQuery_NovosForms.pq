// ============================================================================
//  Power Query (M) — importa os exports mensais do MS Forms de uma PASTA e
//  transforma no formato tidy (fResponses).  Fluxo mensal: salvar o Excel do
//  Forms na pasta -> Página Inicial -> Atualizar Tudo.
//
//  Convenção de nome do arquivo: inclua o período AAAAMM no nome,
//  ex.: "PA_202607.xlsx" ou "2026-07 respostas.xlsx".
//
//  IMPORTANTE (testado com o export real de Junho/2026): o texto de uma
//  pergunta às vezes é reformulado de um mês para o outro (ex.: "Qual você
//  acha que deve ser o MAIOR RISCO..." virou "Quais... os MAIORES RISCOS...").
//  Match por texto EXATO trataria isso como pergunta nova e fragmentaria o
//  histórico. Por isso este código faz: 1) match exato (rápido) e, só para o
//  que sobrar, 2) match "parecido" (fuzzy, nativo do Power Query) — e deixa
//  tudo auditável em duas consultas pequenas que você confere 1x por mês.
//
//  Este arquivo define TRÊS consultas. Crie cada uma em:
//    Power BI -> Transformar Dados -> Nova Consulta -> Consulta em Branco
//    -> Editor Avançado -> cole o bloco correspondente -> Nomeie a consulta
//    exatamente como indicado no comentário "NOME DA CONSULTA:".
// ============================================================================


// ============================================================================
// NOME DA CONSULTA: ImportForms_Detalhe
//   (consulta "de trabalho" — pode desmarcar "Habilitar carregamento";
//    as outras duas consultas dependem dela)
// ============================================================================
let
    PASTA = "C:\XP\Pesquisa\Forms",                       // <-- ajuste aqui
    LIMIAR_PARECIDO = 0.80,                               // 0.0–1.0 (mais alto = mais rígido)

    Fonte = Folder.Files(PASTA),
    SoExcel = Table.SelectRows(Fonte, each
        Text.EndsWith([Extension], ".xlsx") and not Text.StartsWith([Name], "~")),

    // extrai o período (AAAAMM) do nome do arquivo
    ComPeriodo = Table.AddColumn(SoExcel, "Periodo", each
        let d = Text.Select([Name], {"0".."9"}) in
        if Text.Length(d) >= 6 then Number.FromText(Text.Start(d, 6)) else null, Int64.Type),

    // lê cada arquivo, promove cabeçalho e faz unpivot das perguntas
    Lido = Table.AddColumn(ComPeriodo, "Dados", each
        let
            wb = Excel.Workbook([Content], true),
            sh = wb{0}[Data],
            hdr = Table.PromoteHeaders(sh, [PromoteAllScalars = true]),
            cols = Table.ColumnNames(hdr),
            // 5 primeiras colunas do Forms são fixas (Id, Início, Conclusão, Email, Nome)
            fixas = List.FirstN(cols, 5),
            unpiv = Table.UnpivotOtherColumns(hdr, fixas, "PerguntaTxt", "RespostaBruta"),
            comId = Table.AddIndexColumn(unpiv, "LinhaForms", 1, 1, Int64.Type)
        in
            comId),

    Expandido = Table.ExpandTableColumn(Lido, "Dados",
        {"PerguntaTxt", "RespostaBruta"}),

    SemVazias = Table.SelectRows(Expandido, each
        [RespostaBruta] <> null and Text.Trim(Text.From([RespostaBruta])) <> ""),

    // multi-escolha (e campos do Forms que sempre vêm com ";" no fim, mesmo
    // quando só uma opção foi marcada): separa por ";" e descarta vazios —
    // funciona igual para pergunta única ou múltipla.
    Separado = Table.ExpandListColumn(
        Table.AddColumn(SemVazias, "AnswerRaw", each
            List.Transform(Text.Split(Text.From([RespostaBruta]), ";"), each Text.Trim(_))),
        "AnswerRaw"),
    SemToken = Table.SelectRows(Separado, each [AnswerRaw] <> null and [AnswerRaw] <> ""),

    // normaliza o texto da pergunta para casar com dimPergunta[ChaveTexto]
    ChaveNorm = Table.AddColumn(SemToken, "ChaveTexto", each
        Text.Lower(Text.Trim(Text.Replace(Text.From([PerguntaTxt]), "#(00A0)", " ")))),

    // 1) MATCH EXATO (rápido, cobre a maioria)
    ComExato = Table.NestedJoin(ChaveNorm, {"ChaveTexto"},
        dimPergunta, {"ChaveTexto"}, "p_exato", JoinKind.LeftOuter),
    ExpExato = Table.ExpandTableColumn(ComExato, "p_exato",
        {"QuestionID", "TextoPT"}, {"QID_exato", "TextoPT_exato"}),

    // separa o que já casou do que sobrou
    JaCasou = Table.SelectRows(ExpExato, each [QID_exato] <> null),
    SemMatch = Table.SelectRows(ExpExato, each [QID_exato] = null),

    // 2) MATCH PARECIDO (fuzzy) só no que sobrou — nativo do Power Query
    ComFuzzy = Table.FuzzyNestedJoin(
        SemMatch, {"ChaveTexto"}, dimPergunta, {"ChaveTexto"}, "p_fuzzy",
        [IgnoreCase = true, IgnoreSpace = true, NumberOfMatches = 1,
         Threshold = LIMIAR_PARECIDO]),
    ExpFuzzy = Table.ExpandTableColumn(ComFuzzy, "p_fuzzy",
        {"QuestionID", "TextoPT"}, {"QID_fuzzy", "TextoPT_fuzzy"}),

    // marca a origem do match para auditoria
    JaCasouMarcado = Table.AddColumn(JaCasou, "MatchTipo", each "Exato"),
    FuzzyMarcado = Table.AddColumn(ExpFuzzy, "MatchTipo", each
        if [QID_fuzzy] <> null then "Parecido" else "NaoEncontrado"),

    // unifica QuestionID/TextoPT casado independente da origem
    Uniao = Table.Combine({
        Table.TransformColumns(
            Table.AddColumn(JaCasouMarcado, "QuestionID", each [QID_exato]),
            {}
        ),
        Table.AddColumn(FuzzyMarcado, "QuestionID", each [QID_fuzzy])
    }),

    ComTextoCasado = Table.AddColumn(Uniao, "TextoPerguntaCasada", each
        if [MatchTipo] = "Exato" then [TextoPT_exato]
        else if [MatchTipo] = "Parecido" then [TextoPT_fuzzy]
        else null),

    // data (1º dia do mês) e RespID único (período + linha do Forms)
    ComData = Table.AddColumn(ComTextoCasado, "Data", each
        #date(Number.IntegerDivide([Periodo], 100), Number.Mod([Periodo], 100), 1), type date),
    ComResp = Table.AddColumn(ComData, "RespID", each
        Text.From([Periodo]) & "-" & Text.From([LinhaForms]), type text),

    Final = Table.SelectColumns(ComResp,
        {"RespID", "Periodo", "Data", "QuestionID", "PerguntaTxt",
         "TextoPerguntaCasada", "MatchTipo", "AnswerRaw"}),
    Tipado = Table.TransformColumnTypes(Final,
        {{"Periodo", Int64.Type}, {"Data", type date}, {"QuestionID", type text},
         {"PerguntaTxt", type text}, {"AnswerRaw", type text}})
in
    Tipado


// ============================================================================
// NOME DA CONSULTA: NovosForms
//   (esta é a que entra no Table.Combine com o histórico — ver GUIA_PowerBI.md)
// ============================================================================
let
    Base = ImportForms_Detalhe,
    ComQID = Table.SelectRows(Base, each [QuestionID] <> null),
    Final = Table.SelectColumns(ComQID, {"RespID", "Periodo", "Data", "QuestionID", "AnswerRaw"})
in
    Final


// ============================================================================
// NOME DA CONSULTA: _AuditoriaCasamentoParecido
//   (confira 1x por mês: perguntas que casaram por semelhança, não por texto
//    igual — garante que nenhuma foi casada com a pergunta errada)
// ============================================================================
let
    Base = ImportForms_Detalhe,
    Parecidos = Table.SelectRows(Base, each [MatchTipo] = "Parecido"),
    Distintos = Table.Distinct(Table.SelectColumns(Parecidos,
        {"QuestionID", "TextoPerguntaCasada", "PerguntaTxt"})),
    Renomeado = Table.RenameColumns(Distintos,
        {{"PerguntaTxt", "TextoNoForms(mês novo)"}, {"TextoPerguntaCasada", "TextoNaBase(histórico)"}})
in
    Renomeado


// ============================================================================
// NOME DA CONSULTA: _PerguntasNaoReconhecidas
//   (perguntas que NÃO casaram nem exato nem parecido — são genuinamente
//    novas; adicione 1 linha em dimPergunta com um QuestionID novo)
// ============================================================================
let
    Base = ImportForms_Detalhe,
    NaoAchou = Table.SelectRows(Base, each [MatchTipo] = "NaoEncontrado"),
    Distintos = Table.Distinct(Table.SelectColumns(NaoAchou, {"PerguntaTxt"}))
in
    Distintos
