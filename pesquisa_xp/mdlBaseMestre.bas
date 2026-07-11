Attribute VB_Name = "mdlBaseMestre"
'===============================================================================
'  BASE MESTRE - Pesquisa XP (historico completo, append-only)
'  Importe este modulo NA BASE MESTRE (PA_Base_Historica.xlsm).
'
'  ImportarForms:
'    1. Le o export .xlsx do MS Forms
'    2. Anexa as respostas na aba "Raw Data" (larga, canonica), casando as
'       colunas por texto EXATO da pergunta; pergunta nova vira coluna nova
'    3. Anexa as mesmas respostas na aba "Respostas" (long, explodida por ';')
'    4. Atualiza o catalogo "Perguntas" (ultima_edicao, novas perguntas com
'       ativa=1)
'
'  Depois de importar aqui, abra a planilha de PRODUCAO e rode AtualizarProducao.
'===============================================================================
Option Explicit

Private Const RAW_SHEET  As String = "Raw Data"
Private Const LONG_SHEET As String = "Respostas"
Private Const CAT_SHEET  As String = "Perguntas"
Private Const PERIOD_COL As Long = 1
Private Const FIRST_QCOL As Long = 6
Private Const LEADING_COLS As Long = 5   ' Forms: Id, Inicio, Conclusao, Email, Nome

Public Sub ImportarForms()
    Dim wsRaw As Worksheet, wsLong As Worksheet, wsCat As Worksheet
    Dim wbForms As Workbook, wsForms As Worksheet
    Dim caminho As Variant, periodoTxt As String, periodo As Double
    Dim mapa() As Long, novas As Collection
    Dim nLinhas As Long, rawNext As Long

    On Error GoTo Falha
    Set wsRaw = ThisWorkbook.Worksheets(RAW_SHEET)
    Set wsLong = ThisWorkbook.Worksheets(LONG_SHEET)
    Set wsCat = ThisWorkbook.Worksheets(CAT_SHEET)

    periodoTxt = InputBox("Periodo da edicao (AAAAMM):", "Base Mestre", Format(Date, "yyyymm"))
    If Len(periodoTxt) = 0 Then Exit Sub
    If Not IsNumeric(periodoTxt) Or Len(periodoTxt) <> 6 Then
        MsgBox "Periodo invalido.", vbExclamation: Exit Sub
    End If
    periodo = CDbl(periodoTxt)
    If Application.WorksheetFunction.CountIf(wsRaw.Columns(PERIOD_COL), periodo) > 0 Then
        If MsgBox("Periodo ja existe. Continuar (duplica)?", vbYesNo + vbExclamation) = vbNo Then Exit Sub
    End If

    caminho = Application.GetOpenFilename("Excel do MS Forms (*.xlsx),*.xlsx", , "Selecione o export do Forms")
    If caminho = False Then Exit Sub

    Application.ScreenUpdating = False
    Set wbForms = Workbooks.Open(CStr(caminho), ReadOnly:=True)
    Set wsForms = wbForms.Worksheets(1)

    Set novas = New Collection
    mapa = MapearColunas(wsForms, wsRaw, novas)
    nLinhas = wsForms.Cells(wsForms.Rows.Count, 1).End(xlUp).Row - 1

    If MsgBox("Importar " & nLinhas & " respostas do periodo " & periodoTxt & _
              " (" & novas.Count & " pergunta(s) nova(s))?", vbYesNo + vbQuestion) = vbNo Then
        wbForms.Close False: Application.ScreenUpdating = True: Exit Sub
    End If

    ' --- 1) anexar na larga ---
    rawNext = wsRaw.Cells(wsRaw.Rows.Count, PERIOD_COL).End(xlUp).Row + 1
    Dim i As Long, fc As Long
    For i = 1 To nLinhas
        wsRaw.Cells(rawNext + i - 1, PERIOD_COL).Value = periodo
        For fc = LBound(mapa) To UBound(mapa)
            If mapa(fc) > 0 Then
                wsRaw.Cells(rawNext + i - 1, mapa(fc)).Value = wsForms.Cells(1 + i, fc).Value
            End If
        Next fc
    Next i

    ' --- 2) anexar na long (explode por ';') ---
    AnexarLong wsRaw, wsLong, periodo, rawNext, rawNext + nLinhas - 1

    ' --- 3) catalogo ---
    AtualizarCatalogo wsCat, wsRaw, periodo, novas

    wbForms.Close False
    Application.ScreenUpdating = True
    MsgBox "Mestre atualizada: " & nLinhas & " respostas do periodo " & periodoTxt & "." & _
           IIf(novas.Count > 0, vbCrLf & novas.Count & " pergunta(s) nova(s) no catalogo (ativa=1).", ""), _
           vbInformation
    Exit Sub
Falha:
    On Error Resume Next
    If Not wbForms Is Nothing Then wbForms.Close False
    Application.ScreenUpdating = True
    MsgBox "Erro: " & Err.Description, vbExclamation
End Sub

Private Function MapearColunas(wsForms As Worksheet, wsRaw As Worksheet, _
                               ByRef novas As Collection) As Long()
    Dim nF As Long, nR As Long, fc As Long, rc As Long
    Dim mapa() As Long, dict As Object
    nF = wsForms.Cells(1, wsForms.Columns.Count).End(xlToLeft).Column
    nR = wsRaw.Cells(1, wsRaw.Columns.Count).End(xlToLeft).Column
    ReDim mapa(1 To nF)
    Set dict = CreateObject("Scripting.Dictionary")
    For rc = FIRST_QCOL To nR
        Dim h As String: h = CStr(wsRaw.Cells(1, rc).Value)
        If Len(h) > 0 And Not dict.Exists(h) Then dict(h) = rc
    Next rc
    For fc = 1 To nF
        If fc = 1 Then
            mapa(fc) = 0
        ElseIf fc <= LEADING_COLS Then
            mapa(fc) = fc
        Else
            Dim k As String: k = CStr(wsForms.Cells(1, fc).Value)
            If Len(k) = 0 Then
                mapa(fc) = 0
            ElseIf dict.Exists(k) Then
                mapa(fc) = dict(k)
            Else
                nR = nR + 1
                wsRaw.Cells(1, nR).Value = k
                dict(k) = nR
                mapa(fc) = nR
                novas.Add k
            End If
        End If
    Next fc
    MapearColunas = mapa
End Function

Private Sub AnexarLong(wsRaw As Worksheet, wsLong As Worksheet, periodo As Double, _
                       r0 As Long, r1 As Long)
    Dim lr As Long, r As Long, c As Long, nR As Long
    Dim v As String, partes() As String, p As Variant
    lr = wsLong.Cells(wsLong.Rows.Count, 1).End(xlUp).Row + 1
    nR = wsRaw.Cells(1, wsRaw.Columns.Count).End(xlToLeft).Column
    For r = r0 To r1
        For c = FIRST_QCOL To nR
            v = CStr(wsRaw.Cells(r, c).Value)
            If Len(v) > 0 Then
                If InStr(v, ";") > 0 Then
                    partes = Split(v, ";")
                Else
                    ReDim partes(0 To 0): partes(0) = v
                End If
                For Each p In partes
                    If Len(Trim$(CStr(p))) > 0 Then
                        wsLong.Cells(lr, 1).Value = periodo
                        wsLong.Cells(lr, 2).Value = r
                        wsLong.Cells(lr, 3).Value = wsRaw.Cells(1, c).Value
                        wsLong.Cells(lr, 4).Value = Trim$(CStr(p))
                        lr = lr + 1
                    End If
                Next p
            End If
        Next c
    Next r
End Sub

Private Sub AtualizarCatalogo(wsCat As Worksheet, wsRaw As Worksheet, _
                              periodo As Double, novas As Collection)
    Dim ult As Long, r As Long, dict As Object
    Dim nR As Long, c As Long
    Set dict = CreateObject("Scripting.Dictionary")
    ult = wsCat.Cells(wsCat.Rows.Count, 2).End(xlUp).Row
    For r = 2 To ult
        dict(CStr(wsCat.Cells(r, 2).Value)) = r
    Next r
    ' perguntas respondidas neste periodo -> ultima_edicao = periodo
    nR = wsRaw.Cells(1, wsRaw.Columns.Count).End(xlToLeft).Column
    For c = FIRST_QCOL To nR
        Dim h As String: h = CStr(wsRaw.Cells(1, c).Value)
        If Len(h) > 0 Then
            If TemRespostaNoPeriodo(wsRaw, c, periodo) Then
                If dict.Exists(h) Then
                    wsCat.Cells(dict(h), 4).Value = periodo
                Else
                    ult = ult + 1
                    wsCat.Cells(ult, 1).Value = ColLetra(c)
                    wsCat.Cells(ult, 2).Value = h
                    wsCat.Cells(ult, 3).Value = periodo
                    wsCat.Cells(ult, 4).Value = periodo
                    wsCat.Cells(ult, 6).Value = 1
                End If
            End If
        End If
    Next c
End Sub

Private Function TemRespostaNoPeriodo(wsRaw As Worksheet, col As Long, periodo As Double) As Boolean
    Dim ult As Long, r As Long
    ult = wsRaw.Cells(wsRaw.Rows.Count, PERIOD_COL).End(xlUp).Row
    For r = ult To 2 Step -1                       ' respostas novas estao no fim
        If wsRaw.Cells(r, PERIOD_COL).Value <> periodo Then Exit For
        If Len(CStr(wsRaw.Cells(r, col).Value)) > 0 Then
            TemRespostaNoPeriodo = True: Exit Function
        End If
    Next r
End Function

Private Function ColLetra(col As Long) As String
    Dim s As String
    Do While col > 0
        s = Chr(65 + (col - 1) Mod 26) & s
        col = (col - 1) \ 26
    Loop
    ColLetra = s
End Function
