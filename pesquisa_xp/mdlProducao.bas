Attribute VB_Name = "mdlProducao"
'===============================================================================
'  PLANILHA DE PRODUCAO - Pesquisa XP (enxuta; gera o relatorio)
'  Importe este modulo NA PLANILHA DE PRODUCAO (a PA_Principal enxuta).
'
'  AtualizarProducao:
'    1. Atualiza o Power Query (recarrega da mestre: perguntas ativas x N meses)
'    2. Cria a nova coluna de edicao na aba "Base" (periodo/total/data/nome)
'    3. Atualiza o ponteiro de data da aba "Charts"
'    4. Gera log de alternativas novas (aparecem no mes, faltam na Base)
'
'  Fluxo mensal: ImportarForms na MESTRE -> AtualizarProducao AQUI.
'===============================================================================
Option Explicit

Private Const RAW_SHEET    As String = "Raw Data"
Private Const BASE_SHEET   As String = "Base"
Private Const CHARTS_SHEET As String = "Charts"
Private Const LOG_SHEET    As String = "_Log Atualizacao"
Private Const PERIOD_COL   As Long = 1
Private Const FIRST_QCOL   As Long = 6
Private Const BASE_PERIOD_ROW As Long = 1
Private Const BASE_TOTAL_ROW  As Long = 2
Private Const BASE_NAME_ROW   As Long = 3
Private Const BASE_DATE_ROW   As Long = 4

Public Sub AtualizarProducao()
    Dim wsRaw As Worksheet, wsBase As Worksheet, wsCharts As Worksheet
    Dim periodo As Double, total As Long, nomeEd As String

    On Error GoTo Falha
    Set wsRaw = ThisWorkbook.Worksheets(RAW_SHEET)
    Set wsBase = ThisWorkbook.Worksheets(BASE_SHEET)
    On Error Resume Next
    Set wsCharts = ThisWorkbook.Worksheets(CHARTS_SHEET)
    On Error GoTo Falha

    ' 1) refresh do Power Query (sincrono)
    Application.StatusBar = "Atualizando da base mestre (Power Query)..."
    RefreshSincrono

    ' 2) periodo mais recente carregado + total de respostas
    periodo = UltimoPeriodo(wsRaw)
    total = ContarPeriodo(wsRaw, periodo)
    If periodo = 0 Or total = 0 Then
        MsgBox "Nao encontrei respostas apos o refresh. Confira o caminho da mestre na tabela Config.", vbExclamation
        GoTo Fim
    End If

    ' 3) nova coluna de edicao na Base (se ainda nao existe)
    If Not PeriodoJaNaBase(wsBase, periodo) Then
        nomeEd = InputBox("Nome da edicao:", "Producao", _
                          "Edicao de " & Format(DataDoPeriodo(periodo), "mmmm/yyyy"))
        AdicionarColunaEdicao wsBase, periodo, total, DataDoPeriodo(periodo), nomeEd
    End If

    ' 4) ponteiro dos Charts
    If Not wsCharts Is Nothing Then wsCharts.Range("A1").Value = DataDoPeriodo(periodo)

    ' 5) log de alternativas novas
    GerarLogAlternativas wsRaw, wsBase, periodo

    Application.CalculateFull
Fim:
    Application.StatusBar = False
    MsgBox "Producao atualizada para o periodo " & CStr(periodo) & " (" & total & " respostas)." & _
           vbCrLf & "Confira a aba '" & LOG_SHEET & "'.", vbInformation
    Exit Sub
Falha:
    Application.StatusBar = False
    MsgBox "Erro: " & Err.Description, vbExclamation
End Sub

Private Sub RefreshSincrono()
    Dim conn As WorkbookConnection
    For Each conn In ThisWorkbook.Connections
        On Error Resume Next
        conn.OLEDBConnection.BackgroundQuery = False
        On Error GoTo 0
    Next conn
    ThisWorkbook.RefreshAll
    DoEvents
End Sub

Private Function UltimoPeriodo(wsRaw As Worksheet) As Double
    Dim ult As Long, r As Long, m As Double
    ult = wsRaw.Cells(wsRaw.Rows.Count, PERIOD_COL).End(xlUp).Row
    For r = 2 To ult
        If IsNumeric(wsRaw.Cells(r, PERIOD_COL).Value) Then
            If wsRaw.Cells(r, PERIOD_COL).Value > m Then m = wsRaw.Cells(r, PERIOD_COL).Value
        End If
    Next r
    UltimoPeriodo = m
End Function

Private Function ContarPeriodo(wsRaw As Worksheet, periodo As Double) As Long
    ContarPeriodo = Application.WorksheetFunction.CountIf(wsRaw.Columns(PERIOD_COL), periodo)
End Function

Private Function PeriodoJaNaBase(wsBase As Worksheet, periodo As Double) As Boolean
    Dim c As Long
    c = wsBase.Cells(BASE_DATE_ROW, wsBase.Columns.Count).End(xlToLeft).Column
    PeriodoJaNaBase = (wsBase.Cells(BASE_PERIOD_ROW, c).Value = periodo)
End Function

Private Sub AdicionarColunaEdicao(wsBase As Worksheet, periodo As Double, _
                                  total As Long, dataEd As Double, nomeEd As String)
    Dim ult As Long, nova As Long
    ult = wsBase.Cells(BASE_DATE_ROW, wsBase.Columns.Count).End(xlToLeft).Column
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

'--- log de alternativas novas --------------------------------------------------
Private Sub GerarLogAlternativas(wsRaw As Worksheet, wsBase As Worksheet, periodo As Double)
    Dim ws As Worksheet, r As Long
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(LOG_SHEET)
    On Error GoTo 0
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        ws.Name = LOG_SHEET
    End If
    ws.Cells.Clear
    ws.Range("A1").Value = "Alternativas novas no periodo " & CStr(periodo) & " (" & Now & ")"
    ws.Range("A1").Font.Bold = True
    r = 3

    Dim ultB As Long, br As Long, rr As Long
    ultB = wsBase.Cells(wsBase.Rows.Count, 3).End(xlUp).Row
    br = 1
    Do While br <= ultB
        If IsNumeric(wsBase.Cells(br, 2).Value) And Len(wsBase.Cells(br, 3).Value) > 0 _
           And Not IsEmpty(wsBase.Cells(br, 2).Value) Then
            Dim qText As String, rawCol As Long
            qText = CStr(wsBase.Cells(br, 3).Value)
            rawCol = ColunaRawPorTexto(wsRaw, qText)
            Dim conhecidas As Object: Set conhecidas = CreateObject("Scripting.Dictionary")
            rr = br + 1
            Do While rr <= ultB
                If IsNumeric(wsBase.Cells(rr, 2).Value) And Len(wsBase.Cells(rr, 3).Value) > 0 Then Exit Do
                Dim lab As String: lab = Trim$(CStr(wsBase.Cells(rr, 3).Value))
                If Len(lab) > 0 Then conhecidas(LCase$(lab)) = True
                rr = rr + 1
            Loop
            If rawCol > 0 Then
                Dim vistas As Object, v As Variant
                Set vistas = ValoresDistintos(wsRaw, rawCol, periodo)
                For Each v In vistas.Keys
                    If Not conhecidas.Exists(LCase$(Trim$(CStr(v)))) Then
                        ws.Cells(r, 1).Value = "- [" & Left$(qText, 55) & "]"
                        ws.Cells(r, 2).Value = CStr(v)
                        r = r + 1
                    End If
                Next v
            End If
            br = rr
        Else
            br = br + 1
        End If
    Loop
    If r = 3 Then ws.Cells(r, 1).Value = "(nenhuma)"
    ws.Columns("A:B").AutoFit
End Sub

Private Function ValoresDistintos(wsRaw As Worksheet, col As Long, periodo As Double) As Object
    Dim d As Object, ult As Long, i As Long, s As String, partes() As String, p As Variant
    Set d = CreateObject("Scripting.Dictionary")
    ult = wsRaw.Cells(wsRaw.Rows.Count, PERIOD_COL).End(xlUp).Row
    For i = 2 To ult
        If wsRaw.Cells(i, PERIOD_COL).Value = periodo Then
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
    Set ValoresDistintos = d
End Function

Private Function ColunaRawPorTexto(wsRaw As Worksheet, texto As String) As Long
    Dim c As Long, n As Long
    n = wsRaw.Cells(1, wsRaw.Columns.Count).End(xlToLeft).Column
    For c = FIRST_QCOL To n
        If CStr(wsRaw.Cells(1, c).Value) = texto Then
            ColunaRawPorTexto = c: Exit Function
        End If
    Next c
End Function

Private Function DataDoPeriodo(periodo As Double) As Double
    Dim a As Integer, m As Integer
    a = Int(periodo / 100): m = periodo - a * 100
    DataDoPeriodo = DateSerial(a, m, 1)
End Function
