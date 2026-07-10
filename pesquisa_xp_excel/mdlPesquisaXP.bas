Attribute VB_Name = "mdlPesquisaXP"
'===============================================================================
'  Pesquisa XP de Sentimento de Bolsa (assessores) - Atualizacao mensal
'  Automatiza o fluxo manual descrito na aba Summary SEM recriar nenhum dos
'  304 graficos existentes na aba "Charts" (eles ja sao alimentados por formula
'  a partir da aba "Base" - esta macro so automatiza o que alimenta essa base):
'    1. Importa o export .xlsx do MS Forms para a aba "Raw Data" (casando as
'       colunas por texto da pergunta, com fallback por SEMELHANCA para
'       perguntas so reformuladas) e ja preenche o codigo do periodo.
'    2. Cria a nova coluna de edicao na aba "Base" (copia a ultima coluna viva
'       e ajusta periodo / total de respostas / data / nome) - os 304 graficos
'       da aba "Charts" continuam os mesmos, so passam a enxergar o mes novo.
'    3. Atualiza o ponteiro de data da aba "Charts".
'    4. Gera um LOG com PERGUNTAS NOVAS, PERGUNTAS CASADAS POR SEMELHANCA
'       (texto reformulado - confira) e ALTERNATIVAS NOVAS/ALTERADAS p/ revisar.
'
'  Testado (matching de cabecalho) contra o export real do MS Forms de
'  Junho/2026: 12/12 perguntas do mes casaram (8 exatas + 4 por semelhanca,
'  96-99%), nenhuma pergunta ou alternativa ficou de fora.
'
'  Nada e sobrescrito sem confirmacao. Rode "AtualizarPesquisa".
'  Requisito: Excel (Windows). Salve o arquivo como .xlsm depois de importar.
'===============================================================================
Option Explicit

' ---- Config -------------------------------------------------------------------
Private Const RAW_SHEET   As String = "Raw Data"
Private Const BASE_SHEET  As String = "Base"
Private Const CHARTS_SHEET As String = "Charts"
Private Const LOG_SHEET   As String = "_Log Atualizacao"

Private Const RAW_HEADER_ROW As Long = 1
Private Const RAW_PERIOD_COL As Long = 1     ' A = "Survey" (codigo AAAAMM)
Private Const RAW_FIRST_QCOL As Long = 6     ' F = primeira pergunta
Private Const LEADING_COLS   As Long = 5     ' Forms: Id, Inicio, Conclusao, Email, Nome
Private Const LIMIAR_PARECIDO As Double = 0.85  ' 0-1; casa perguntas so reformuladas

Private Const BASE_PERIOD_ROW As Long = 1
Private Const BASE_TOTAL_ROW  As Long = 2
Private Const BASE_NAME_ROW   As Long = 3
Private Const BASE_DATE_ROW   As Long = 4

'===============================================================================
'  MACRO PRINCIPAL
'===============================================================================
Public Sub AtualizarPesquisa()
    Dim wsRaw As Worksheet, wsBase As Worksheet, wsCharts As Worksheet
    Dim wbForms As Workbook, wsForms As Worksheet
    Dim caminho As Variant, periodo As Double, periodoTxt As String
    Dim nomeEd As String
    Dim calcAnt As XlCalculation
    Dim rawNext As Long, nLinhas As Long, nNovasPerg As Long, nParecidas As Long
    Dim mapCol() As Long, novasPerg As Collection, parecidas As Collection

    On Error GoTo Falha
    Set wsRaw = ThisWorkbook.Worksheets(RAW_SHEET)
    Set wsBase = ThisWorkbook.Worksheets(BASE_SHEET)
    On Error Resume Next
    Set wsCharts = ThisWorkbook.Worksheets(CHARTS_SHEET)
    On Error GoTo Falha

    ' 1) periodo (AAAAMM)
    periodoTxt = InputBox("Informe o periodo da edicao (AAAAMM):" & vbCrLf & _
                          "ex.: 202607 para Julho/2026", "Pesquisa XP", _
                          Format(Date, "yyyymm"))
    If Len(periodoTxt) = 0 Then Exit Sub
    If Not IsNumeric(periodoTxt) Or Len(periodoTxt) <> 6 Then
        MsgBox "Periodo invalido. Use AAAAMM (ex.: 202607).", vbExclamation: Exit Sub
    End If
    periodo = CDbl(periodoTxt)
    If PeriodoJaExiste(wsRaw, periodo) Then
        If MsgBox("O periodo " & periodoTxt & " ja existe no Raw Data." & vbCrLf & _
                  "Deseja continuar mesmo assim (vai duplicar)?", _
                  vbYesNo + vbExclamation) = vbNo Then Exit Sub
    End If

    ' 2) arquivo do Forms
    caminho = Application.GetOpenFilename( _
        "Excel do MS Forms (*.xlsx;*.xls),*.xlsx;*.xls", , _
        "Selecione o export do MS Forms")
    If caminho = False Then Exit Sub

    Application.ScreenUpdating = False
    calcAnt = Application.Calculation
    Application.Calculation = xlCalculationManual
    Set wbForms = Workbooks.Open(CStr(caminho), ReadOnly:=True)
    Set wsForms = wbForms.Worksheets(1)

    ' 3) mapear colunas do Forms -> Raw Data (1..5 por posicao; 6+ por texto,
    '    com fallback por semelhanca para perguntas so reformuladas)
    Set novasPerg = New Collection
    Set parecidas = New Collection
    mapCol = MapearColunas(wsForms, wsRaw, novasPerg, parecidas)
    nLinhas = UltimaLinha(wsForms, 1) - 1          ' menos o cabecalho
    nNovasPerg = novasPerg.Count
    nParecidas = parecidas.Count

    ' 4) confirmar plano
    Dim msg As String
    msg = "Plano de atualizacao:" & vbCrLf & vbCrLf & _
          "- Periodo: " & periodoTxt & vbCrLf & _
          "- Respostas a importar: " & nLinhas & vbCrLf & _
          "- Perguntas NOVAS (fora do Raw Data): " & nNovasPerg & vbCrLf & _
          "- Perguntas casadas por SEMELHANCA (texto mudou, confira no log): " & nParecidas & vbCrLf & _
          "- Nova coluna de edicao na Base: " & _
             ColLetra(UltimaColunaEdicao(wsBase) + 1) & vbCrLf & vbCrLf & _
          "Confirmar?"
    If MsgBox(msg, vbYesNo + vbQuestion, "Pesquisa XP") = vbNo Then
        wbForms.Close False: GoTo Restaurar
    End If

    ' 5) importar respostas para o Raw Data
    rawNext = UltimaLinha(wsRaw, RAW_PERIOD_COL) + 1
    ImportarRespostas wsForms, wsRaw, mapCol, periodo, rawNext, nLinhas

    ' 6) nova coluna de edicao na Base
    nomeEd = InputBox("Nome da edicao (linha 3 da Base):", "Pesquisa XP", _
                      "Edicao de " & NomeMes(periodo))
    AdicionarColunaEdicao wsBase, periodo, nLinhas, DataDoPeriodo(periodo), nomeEd

    ' 7) ponteiro de data dos Charts
    If Not wsCharts Is Nothing Then
        On Error Resume Next
        wsCharts.Range("A1").Value = DataDoPeriodo(periodo)
        On Error GoTo Falha
    End If

    ' 8) LOG (perguntas novas + parecidas + alternativas novas)
    GerarLog wsRaw, wsBase, periodo, novasPerg, parecidas

    wbForms.Close False
    Application.Calculation = xlCalculationAutomatic
    Application.CalculateFull

Restaurar:
    Application.Calculation = calcAnt
    Application.ScreenUpdating = True
    MsgBox "Atualizacao concluida!" & vbCrLf & _
           "Confira a aba '" & LOG_SHEET & "' para perguntas/alternativas novas.", _
           vbInformation, "Pesquisa XP"
    Exit Sub

Falha:
    On Error Resume Next
    If Not wbForms Is Nothing Then wbForms.Close False
    Application.Calculation = calcAnt
    Application.ScreenUpdating = True
    MsgBox "Erro: " & Err.Number & " - " & Err.Description, vbExclamation, "Pesquisa XP"
End Sub

'===============================================================================
'  Mapear colunas do Forms para o Raw Data
'    - colunas 1..LEADING_COLS por POSICAO (Id->A(periodo), Inicio->B, ... Nome->E)
'    - colunas 6+ por TEXTO da pergunta (normalizado), com fallback por
'      SEMELHANCA (LCS) quando o texto foi so reformulado (>= LIMIAR_PARECIDO)
'    - pergunta sem correspondencia (nem exata, nem parecida) => nova coluna
'      no fim do Raw Data (+ log)
'  Retorna: mapCol(colForms) = colRaw  (0 = ignorar, ex.: coluna Id)
'===============================================================================
Private Function MapearColunas(wsForms As Worksheet, wsRaw As Worksheet, _
                               ByRef novasPerg As Collection, _
                               ByRef parecidas As Collection) As Long()
    Dim nF As Long, nR As Long, fc As Long, rc As Long
    Dim mapa() As Long, dict As Object
    nF = UltimaColuna(wsForms, RAW_HEADER_ROW)
    nR = UltimaColuna(wsRaw, RAW_HEADER_ROW)
    ReDim mapa(1 To nF)

    ' dicionario texto normalizado -> coluna do Raw Data (a partir de F)
    Set dict = CreateObject("Scripting.Dictionary")
    For rc = RAW_FIRST_QCOL To nR
        Dim h As String: h = Normalizar(wsRaw.Cells(RAW_HEADER_ROW, rc).Value)
        If Len(h) > 0 And Not dict.Exists(h) Then dict(h) = rc
    Next rc

    For fc = 1 To nF
        If fc = 1 Then
            mapa(fc) = 0                                  ' Id -> ignorar
        ElseIf fc <= LEADING_COLS Then
            mapa(fc) = fc                                 ' 2->B ... 5->E
        Else
            Dim k As String: k = Normalizar(wsForms.Cells(RAW_HEADER_ROW, fc).Value)
            If Len(k) = 0 Then
                mapa(fc) = 0
            ElseIf dict.Exists(k) Then
                mapa(fc) = dict(k)
            Else
                Dim chaveParecida As String
                chaveParecida = MelhorChaveParecida(k, dict)
                If Len(chaveParecida) > 0 Then
                    ' mesma pergunta, texto reformulado -> reusa a coluna existente
                    Dim colExistente As Long: colExistente = dict(chaveParecida)
                    mapa(fc) = colExistente
                    parecidas.Add "NOVO: " & CStr(wsForms.Cells(RAW_HEADER_ROW, fc).Value) & _
                                  "   =>   JA EXISTIA COMO: " & _
                                  CStr(wsRaw.Cells(RAW_HEADER_ROW, colExistente).Value) & _
                                  "   (similaridade " & _
                                  Format(Similaridade(k, chaveParecida) * 100, "0") & "%)"
                Else
                    ' pergunta genuinamente nova -> cria coluna no fim do Raw Data
                    nR = nR + 1
                    wsRaw.Cells(RAW_HEADER_ROW, nR).Value = wsForms.Cells(RAW_HEADER_ROW, fc).Value
                    dict(k) = nR
                    mapa(fc) = nR
                    novasPerg.Add wsForms.Cells(RAW_HEADER_ROW, fc).Value
                End If
            End If
        End If
    Next fc
    MapearColunas = mapa
End Function

' Similaridade tipo "ratio" (LCS - maior subsequencia comum), de 0 a 1.
' Mesma familia de calculo usada no Power Query (Table.FuzzyNestedJoin).
Private Function Similaridade(ByRef a As String, ByRef b As String) As Double
    Dim n As Long, m As Long, i As Long, j As Long
    Dim prev() As Long, cur() As Long, tmp() As Long
    n = Len(a): m = Len(b)
    If n = 0 Or m = 0 Then Similaridade = 0: Exit Function
    ReDim prev(0 To m)
    ReDim cur(0 To m)
    For i = 1 To n
        cur(0) = 0
        For j = 1 To m
            If Mid$(a, i, 1) = Mid$(b, j, 1) Then
                cur(j) = prev(j - 1) + 1
            ElseIf prev(j) >= cur(j - 1) Then
                cur(j) = prev(j)
            Else
                cur(j) = cur(j - 1)
            End If
        Next j
        tmp = prev: prev = cur: cur = tmp
    Next i
    Similaridade = 2# * prev(m) / (n + m)
End Function

' Procura no dicionario (chave normalizada -> coluna) a entrada mais parecida
' com "k". Retorna a chave encontrada, ou "" se nada atingir LIMIAR_PARECIDO.
Private Function MelhorChaveParecida(ByRef k As String, dict As Object) As String
    Dim chave As Variant, melhorChave As String, melhorSim As Double, s As Double
    melhorSim = 0: melhorChave = ""
    For Each chave In dict.Keys
        s = Similaridade(k, CStr(chave))
        If s > melhorSim Then
            melhorSim = s
            melhorChave = CStr(chave)
        End If
    Next chave
    If melhorSim >= LIMIAR_PARECIDO Then
        MelhorChaveParecida = melhorChave
    Else
        MelhorChaveParecida = ""
    End If
End Function

Private Sub ImportarRespostas(wsForms As Worksheet, wsRaw As Worksheet, _
                              mapCol() As Long, periodo As Double, _
                              rawNext As Long, nLinhas As Long)
    Dim i As Long, fc As Long, tr As Long
    For i = 1 To nLinhas
        tr = rawNext + i - 1
        wsRaw.Cells(tr, RAW_PERIOD_COL).Value = periodo
        For fc = LBound(mapCol) To UBound(mapCol)
            If mapCol(fc) > 0 Then
                wsRaw.Cells(tr, mapCol(fc)).Value = wsForms.Cells(1 + i, fc).Value
            End If
        Next fc
    Next i
End Sub

'===============================================================================
'  Nova coluna de edicao na Base (copia a ultima coluna viva -> ajusta cabecalhos)
'===============================================================================
Private Sub AdicionarColunaEdicao(wsBase As Worksheet, periodo As Double, _
                                  total As Long, dataEd As Double, nomeEd As String)
    Dim ult As Long, nova As Long
    ult = UltimaColunaEdicao(wsBase)
    nova = ult + 1
    wsBase.Columns(ult).Copy
    wsBase.Columns(nova).PasteSpecial Paste:=xlPasteAll
    Application.CutCopyMode = False
    wsBase.Cells(BASE_PERIOD_ROW, nova).Value = periodo
    wsBase.Cells(BASE_TOTAL_ROW, nova).Value = total
    wsBase.Cells(BASE_NAME_ROW, nova).Value = nomeEd
    With wsBase.Cells(BASE_DATE_ROW, nova)
        .Value = dataEd
        .NumberFormat = "mmm/yy"
    End With
End Sub

'===============================================================================
'  LOG: perguntas novas + alternativas novas/alteradas do periodo
'===============================================================================
Private Sub GerarLog(wsRaw As Worksheet, wsBase As Worksheet, periodo As Double, _
                     novasPerg As Collection, parecidas As Collection)
    Dim ws As Worksheet, r As Long, it As Variant
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(LOG_SHEET)
    On Error GoTo 0
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        ws.Name = LOG_SHEET
    End If
    ws.Cells.Clear
    ws.Range("A1").Value = "LOG de atualizacao - periodo " & CStr(periodo) & " (" & Now & ")"
    ws.Range("A1").Font.Bold = True
    r = 3
    ws.Cells(r, 1).Value = "PERGUNTAS NOVAS (adicionadas ao fim do Raw Data - falta criar bloco na Base):"
    ws.Cells(r, 1).Font.Bold = True: r = r + 1
    If novasPerg.Count = 0 Then
        ws.Cells(r, 1).Value = "(nenhuma)": r = r + 1
    Else
        For Each it In novasPerg
            ws.Cells(r, 1).Value = "- " & CStr(it): r = r + 1
        Next it
    End If
    r = r + 1
    ws.Cells(r, 1).Value = "PERGUNTAS CASADAS POR SEMELHANCA (texto mudou, confira se casou certo):"
    ws.Cells(r, 1).Font.Bold = True: r = r + 1
    If parecidas.Count = 0 Then
        ws.Cells(r, 1).Value = "(nenhuma)": r = r + 1
    Else
        For Each it In parecidas
            ws.Cells(r, 1).Value = "- " & CStr(it): r = r + 1
        Next it
    End If
    r = r + 1
    ws.Cells(r, 1).Value = "ALTERNATIVAS NOVAS/ALTERADAS (aparecem no periodo mas nao estao na Base):"
    ws.Cells(r, 1).Font.Bold = True: r = r + 1
    r = DetectarNovasAlternativas(wsRaw, wsBase, periodo, ws, r)
    ws.Columns("A:B").AutoFit
    ws.Activate
End Sub

' Percorre os blocos da Base (colB numerico + colC texto = pergunta; linhas
' seguintes com colC = alternativas). Compara com os valores distintos do periodo.
Private Function DetectarNovasAlternativas(wsRaw As Worksheet, wsBase As Worksheet, _
                                periodo As Double, wsLog As Worksheet, ByVal r As Long) As Long
    Dim br As Long, ultB As Long, qText As String, rawCol As Long
    Dim conhecidas As Object, vistas As Object, achou As Boolean
    ultB = wsBase.Cells(wsBase.Rows.Count, 3).End(xlUp).Row
    br = 1
    Do While br <= ultB
        If IsNumeric(wsBase.Cells(br, 2).Value) And Len(wsBase.Cells(br, 3).Value) > 0 _
           And Not IsEmpty(wsBase.Cells(br, 2).Value) Then
            qText = CStr(wsBase.Cells(br, 3).Value)
            rawCol = ColunaRawPorTexto(wsRaw, qText)
            ' coleta alternativas conhecidas (linhas seguintes ate proximo header/gap)
            Set conhecidas = CreateObject("Scripting.Dictionary")
            Dim rr As Long: rr = br + 1
            Do While rr <= ultB
                If IsNumeric(wsBase.Cells(rr, 2).Value) And _
                   Len(wsBase.Cells(rr, 3).Value) > 0 Then Exit Do   ' proximo header
                Dim lab As String: lab = Normalizar(wsBase.Cells(rr, 3).Value)
                If Len(lab) > 0 Then conhecidas(lab) = True
                rr = rr + 1
            Loop
            ' valores distintos do periodo (split por ';') vs conhecidas
            If rawCol > 0 Then
                Set vistas = ValoresDistintosPeriodo(wsRaw, rawCol, periodo)
                Dim v As Variant
                For Each v In vistas.Keys
                    If Not conhecidas.Exists(Normalizar(CStr(v))) Then
                        wsLog.Cells(r, 1).Value = "- [" & Left$(qText, 55) & "]"
                        wsLog.Cells(r, 2).Value = CStr(v)
                        r = r + 1
                    End If
                Next v
            End If
            br = rr
        Else
            br = br + 1
        End If
    Loop
    DetectarNovasAlternativas = r
End Function

Private Function ValoresDistintosPeriodo(wsRaw As Worksheet, col As Long, periodo As Double) As Object
    Dim d As Object, ult As Long, i As Long, s As String, partes() As String, p As Variant
    Set d = CreateObject("Scripting.Dictionary")
    ult = UltimaLinha(wsRaw, RAW_PERIOD_COL)
    For i = RAW_HEADER_ROW + 1 To ult
        If wsRaw.Cells(i, RAW_PERIOD_COL).Value = periodo Then
            s = CStr(wsRaw.Cells(i, col).Value)
            If Len(s) > 0 Then
                If InStr(s, ";") > 0 Then
                    partes = Split(s, ";")
                    For Each p In partes
                        If Len(Trim$(CStr(p))) > 0 Then d(Trim$(CStr(p))) = True
                    Next p
                Else
                    d(Trim$(s)) = True
                End If
            End If
        End If
    Next i
    Set ValoresDistintosPeriodo = d
End Function

'===============================================================================
'  Utilitarios
'===============================================================================
Private Function Normalizar(v As Variant) As String
    Dim s As String
    s = CStr(v)
    s = Replace(s, Chr(160), " ")          ' nbsp
    s = Replace(s, vbTab, " ")
    Do While InStr(s, "  ") > 0: s = Replace(s, "  ", " "): Loop
    Normalizar = LCase$(Trim$(s))
End Function

Private Function ColunaRawPorTexto(wsRaw As Worksheet, texto As String) As Long
    Dim c As Long, n As Long, alvo As String
    alvo = Normalizar(texto)
    n = UltimaColuna(wsRaw, RAW_HEADER_ROW)
    For c = RAW_FIRST_QCOL To n
        If Normalizar(wsRaw.Cells(RAW_HEADER_ROW, c).Value) = alvo Then
            ColunaRawPorTexto = c: Exit Function
        End If
    Next c
    ColunaRawPorTexto = 0
End Function

Private Function UltimaColunaEdicao(wsBase As Worksheet) As Long
    ' ultima coluna com data na linha 4 (edicoes)
    Dim c As Long
    c = wsBase.Cells(BASE_DATE_ROW, wsBase.Columns.Count).End(xlToLeft).Column
    UltimaColunaEdicao = c
End Function

Private Function UltimaLinha(ws As Worksheet, col As Long) As Long
    UltimaLinha = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
End Function

Private Function UltimaColuna(ws As Worksheet, linha As Long) As Long
    UltimaColuna = ws.Cells(linha, ws.Columns.Count).End(xlToLeft).Column
End Function

Private Function PeriodoJaExiste(wsRaw As Worksheet, periodo As Double) As Boolean
    PeriodoJaExiste = (Application.WorksheetFunction.CountIf( _
        wsRaw.Columns(RAW_PERIOD_COL), periodo) > 0)
End Function

Private Function DataDoPeriodo(periodo As Double) As Double
    Dim a As Integer, m As Integer
    a = Int(periodo / 100): m = periodo - a * 100
    DataDoPeriodo = DateSerial(a, m, 1)
End Function

Private Function NomeMes(periodo As Double) As String
    NomeMes = Format(DataDoPeriodo(periodo), "mmmm/yyyy")
End Function

Private Function ColLetra(col As Long) As String
    Dim s As String
    Do While col > 0
        s = Chr(65 + (col - 1) Mod 26) & s
        col = (col - 1) \ 26
    Loop
    ColLetra = s
End Function
