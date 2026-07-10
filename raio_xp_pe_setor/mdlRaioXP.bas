Attribute VB_Name = "mdlRaioXP"
'===============================================================================
'  Raio-XP da Bolsa - P/E (12m fwd) por Setor via Bloomberg
'  Modulo de automacao / Automation module
'
'  Fluxo (1 clique): AtualizarTudo
'    1. Le a data de fechamento em Painel!C4
'    2. (Re)escreve as formulas BDH nas abas Data_* (puxa 10 anos de P/E 12m fwd)
'    3. Espera o Bloomberg terminar de carregar
'    4. Congela o historico em valores (opcional) e recalcula
'    5. Desenha as barras (min-max com bolinha no atual) em todas as tabelas
'    6. Carimba a data/hora da atualizacao
'
'  Requisitos: Excel com o add-in do Bloomberg (BDH) ativo.
'===============================================================================
Option Explicit

' ---- Config -----------------------------------------------------------------
Private Const CONGELAR_HISTORICO As Boolean = True   ' True = cola valores (rapido/portatil)
Private Const TIMEOUT_SEG As Long = 180              ' espera max. do Bloomberg (segundos)
Private Const DATA_R0 As Long = 5                    ' 1a linha de dados nas abas Data_*
Private Const DATA_R1 As Long = 125                  ' ultima linha (121 meses = 10 anos)
Private Const ST_MAX As Long = 127
Private Const ST_MIN As Long = 128
Private Const ST_AVG As Long = 129
Private Const ST_CUR As Long = 130

Private Const COR_LINHA As Long = 4210752            ' RGB(64,64,64) cinza escuro
Private Const COR_PONTO As Long = 14660238           ' RGB(142,179,223) azul claro (8EB3DF)

Private Const OVR As String = _
  """per"",""cm"",""Days"",""A"",""Fill"",""P"",""BEST_DATA_SOURCE_OVERRIDE"",""bst"",""CDR"",""BZ"",""BEST_FPERIOD_OVERRIDE"",""bf"""

Private Const DATA_SHEETS As String = "Data_BR|Data_LATAM|Data_EM|Data_World"

'===============================================================================
'  ENTRADA PRINCIPAL - atribua este macro ao botao "ATUALIZAR / UPDATE"
'===============================================================================
Public Sub AtualizarTudo()
    Dim calcMode As XlCalculation
    Dim t0 As Double
    Dim arr() As String, i As Long

    On Error GoTo Falha
    If Not ConfirmarBloomberg() Then Exit Sub

    ' --- salva estado do app ---
    calcMode = Application.Calculation
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.DisplayAlerts = False
    Application.Calculation = xlCalculationManual
    Application.StatusBar = "Preparando formulas Bloomberg..."

    arr = Split(DATA_SHEETS, "|")

    ' 1) (re)escreve as formulas BDH para puxar tudo de novo na data atual
    For i = LBound(arr) To UBound(arr)
        PrepararFormulasBDH ThisWorkbook.Worksheets(arr(i))
    Next i

    ' 2) forca o recalculo e espera o Bloomberg carregar
    Application.StatusBar = "Solicitando dados ao Bloomberg..."
    ForcarRefreshBloomberg
    Application.Calculation = xlCalculationAutomatic
    Application.CalculateFull
    EsperarBloomberg TIMEOUT_SEG

    ' 3) congela o historico em valores (opcional)
    If CONGELAR_HISTORICO Then
        Application.StatusBar = "Congelando historico em valores..."
        For i = LBound(arr) To UBound(arr)
            CongelarValores ThisWorkbook.Worksheets(arr(i))
        Next i
    End If

    ' 4) recalcula tabelas e desenha as barras
    Application.CalculateFull
    Application.StatusBar = "Desenhando as barras (min-max)..."
    DesenharTodasAsBarras

    ' 5) carimbo de atualizacao
    With ThisWorkbook.Worksheets("Painel").Range("C8")
        .Value = Now
        .NumberFormat = "dd/mm/yyyy hh:mm"
    End With

    RestaurarApp calcMode
    Application.StatusBar = False
    MsgBox "Atualizacao concluida!" & vbCrLf & _
           "As abas Consolidated / Consolidado (PT) / Relative / Relativo (PT) " & _
           "estao prontas.", vbInformation, "Raio-XP"
    Exit Sub

Falha:
    RestaurarApp calcMode
    Application.StatusBar = False
    MsgBox "Erro durante a atualizacao:" & vbCrLf & Err.Number & " - " & Err.Description, _
           vbExclamation, "Raio-XP"
End Sub

'===============================================================================
'  Versao "segura": so refaz o refresh + barras, sem congelar o historico
'===============================================================================
Public Sub AtualizarBloomberg_Somente()
    On Error GoTo Falha
    If Not ConfirmarBloomberg() Then Exit Sub
    Application.ScreenUpdating = False
    Application.StatusBar = "Atualizando Bloomberg..."
    ForcarRefreshBloomberg
    Application.CalculateFull
    EsperarBloomberg TIMEOUT_SEG
    DesenharTodasAsBarras
    Application.ScreenUpdating = True
    Application.StatusBar = False
    MsgBox "Refresh concluido (historico nao foi congelado).", vbInformation, "Raio-XP"
    Exit Sub
Falha:
    Application.ScreenUpdating = True
    Application.StatusBar = False
    MsgBox "Erro: " & Err.Description, vbExclamation, "Raio-XP"
End Sub

'-------------------------------------------------------------------------------
'  (Re)escreve as formulas BDH de coluna nas abas de dados
'-------------------------------------------------------------------------------
Private Sub PrepararFormulasBDH(ws As Worksheet)
    Dim c As Long
    ' limpa a grade antiga
    ws.Range(ws.Cells(DATA_R0, 1), ws.Cells(DATA_R1, 12)).ClearContents
    ' A5: indice -> data + valor (spill A5:B125)
    ws.Cells(DATA_R0, 1).Formula = _
        "=BDH($B$4,""BEST_PE_RATIO"",$D$1,$B$1,""Dates"",""S""," & OVR & ")"
    ' C5..L5: setores, valor apenas (spill vertical)
    For c = 3 To 12
        ws.Cells(DATA_R0, c).Formula = _
            "=BDH(" & ws.Cells(4, c).Address(False, True) & _
            ",""BEST_PE_RATIO"",$D$1,$B$1,""Dates"",""H""," & OVR & ")"
    Next c
End Sub

'-------------------------------------------------------------------------------
'  Congela A5:L125 em valores (remove as formulas BDH depois de carregado)
'-------------------------------------------------------------------------------
Private Sub CongelarValores(ws As Worksheet)
    Dim rng As Range
    Set rng = ws.Range(ws.Cells(DATA_R0, 1), ws.Cells(DATA_R1, 12))
    rng.Copy
    rng.PasteSpecial Paste:=xlPasteValues
    Application.CutCopyMode = False
End Sub

'-------------------------------------------------------------------------------
'  Tenta acionar o refresh do Bloomberg (nomes variam por versao do add-in)
'-------------------------------------------------------------------------------
Private Sub ForcarRefreshBloomberg()
    On Error Resume Next
    Application.Run "RefreshAllStaticData"
    Application.Run "BLP_RefreshAllWorkbooks"
    Application.Run "RefreshEntireWorkbook"
    On Error GoTo 0
End Sub

'-------------------------------------------------------------------------------
'  Espera o Bloomberg terminar (celulas deixam de ser texto "Requesting..." / erro)
'-------------------------------------------------------------------------------
Private Sub EsperarBloomberg(ByVal timeoutSeg As Long)
    Dim t0 As Double, pend As Long
    Dim arr() As String, i As Long, r As Long, c As Long
    Dim v As Variant
    arr = Split(DATA_SHEETS, "|")
    t0 = Timer
    Do
        pend = 0
        For i = LBound(arr) To UBound(arr)
            With ThisWorkbook.Worksheets(arr(i))
                ' amostra: primeira e ultima linha de dados, colunas B..L
                For r = DATA_R0 To DATA_R1 Step (DATA_R1 - DATA_R0)
                    For c = 2 To 12
                        v = .Cells(r, c).Value
                        If IsError(v) Then
                            pend = pend + 1
                        ElseIf VarType(v) = vbString Then
                            If InStr(1, v, "Requesting", vbTextCompare) > 0 _
                               Or InStr(1, v, "#N/A", vbTextCompare) > 0 _
                               Or v = "" Then pend = pend + 1
                        End If
                    Next c
                Next r
            End With
        Next i
        If pend = 0 Then Exit Do
        DoEvents
        Application.Wait Now + TimeSerial(0, 0, 1)
    Loop While (Timer - t0) < timeoutSeg
End Sub

'===============================================================================
'  DESENHO DAS BARRAS (min-max com bolinha no valor atual)
'===============================================================================
Public Sub DesenharTodasAsBarras()
    Dim relEN As Worksheet, relPT As Worksheet
    Dim conEN As Worksheet, conPT As Worksheet
    Set relEN = ThisWorkbook.Worksheets("Relative")
    Set relPT = ThisWorkbook.Worksheets("Relativo (PT)")
    Set conEN = ThisWorkbook.Worksheets("Consolidated")
    Set conPT = ThisWorkbook.Worksheets("Consolidado (PT)")

    ' --- tabelas relativas (3 blocos por aba) ---
    DesenharBarras relEN, 5, 15, 4, 6, 7, 8      ' T1: val D, min F, max G, barra H
    DesenharBarras relEN, 20, 30, 3, 5, 6, 7     ' T2: val C, min E, max F, barra G
    DesenharBarras relEN, 35, 45, 3, 5, 6, 7     ' T3
    DesenharBarras relPT, 5, 15, 4, 6, 7, 8
    DesenharBarras relPT, 20, 30, 3, 5, 6, 7
    DesenharBarras relPT, 35, 45, 3, 5, 6, 7

    ' --- consolidado absoluto (4 regioes) ---
    DesenharConsolidado conEN
    DesenharConsolidado conPT
End Sub

Private Sub DesenharConsolidado(ws As Worksheet)
    ' regioes: BR(3), LATAM(8), EM(13), World(18); PE=start, min=start+2, max=start+3, barra=start+4
    Dim st As Variant, starts As Variant
    starts = Array(3, 8, 13, 18)
    For Each st In starts
        DesenharBarras ws, 6, 16, CLng(st), CLng(st) + 2, CLng(st) + 3, CLng(st) + 4
    Next st
End Sub

'-------------------------------------------------------------------------------
'  Desenha uma barra por linha na coluna barCol, entre linhas r0 e r1
'-------------------------------------------------------------------------------
Public Sub DesenharBarras(ws As Worksheet, ByVal r0 As Long, ByVal r1 As Long, _
                          ByVal valCol As Long, ByVal minCol As Long, _
                          ByVal maxCol As Long, ByVal barCol As Long)
    Dim i As Long
    Dim vAtual As Double, vMin As Double, vMax As Double
    Dim cl As Range
    Dim x0 As Single, x1 As Single, xMid As Single, yMid As Single
    Dim mg As Single, capH As Single, dot As Single
    Dim shp As Shape

    LimparBarras ws, barCol, r0, r1

    For i = r0 To r1
        If EhNumero(ws.Cells(i, valCol).Value) And _
           EhNumero(ws.Cells(i, minCol).Value) And _
           EhNumero(ws.Cells(i, maxCol).Value) Then

            vAtual = ws.Cells(i, valCol).Value
            vMin = ws.Cells(i, minCol).Value
            vMax = ws.Cells(i, maxCol).Value
            If vMax <= vMin Then GoTo Prox

            Set cl = ws.Cells(i, barCol)
            mg = cl.Width * 0.12                         ' margem lateral
            x0 = cl.Left + mg
            x1 = cl.Left + cl.Width - mg
            yMid = cl.Top + cl.Height / 2
            ' posicao do ponto (clamp 0..1)
            Dim f As Double
            f = (vAtual - vMin) / (vMax - vMin)
            If f < 0 Then f = 0
            If f > 1 Then f = 1
            xMid = x0 + (x1 - x0) * f

            capH = Application.WorksheetFunction.Min(8, cl.Height - 4)
            dot = Application.WorksheetFunction.Min(6, cl.Height - 4)

            ' linha base min->max
            Set shp = ws.Shapes.AddLine(x0, yMid, x1, yMid)
            MarcarShape shp, barCol
            shp.Line.Weight = 1.75: shp.Line.ForeColor.RGB = COR_LINHA
            ' cap min
            Set shp = ws.Shapes.AddLine(x0, yMid - capH / 2, x0, yMid + capH / 2)
            MarcarShape shp, barCol
            shp.Line.Weight = 1#: shp.Line.ForeColor.RGB = COR_LINHA
            ' cap max
            Set shp = ws.Shapes.AddLine(x1, yMid - capH / 2, x1, yMid + capH / 2)
            MarcarShape shp, barCol
            shp.Line.Weight = 1#: shp.Line.ForeColor.RGB = COR_LINHA
            ' ponto (atual)
            Set shp = ws.Shapes.AddShape(msoShapeOval, xMid - dot / 2, yMid - dot / 2, dot, dot)
            MarcarShape shp, barCol
            shp.Fill.ForeColor.RGB = COR_PONTO
            shp.Line.Visible = msoFalse
        End If
Prox:
    Next i
End Sub

Private Sub MarcarShape(shp As Shape, ByVal barCol As Long)
    shp.Name = "RXP_" & barCol & "_" & shp.ID          ' prefixo para localizar/limpar
    shp.Placement = xlMove
End Sub

Private Sub LimparBarras(ws As Worksheet, ByVal barCol As Long, ByVal r0 As Long, ByVal r1 As Long)
    Dim s As Shape, rng As Range
    Set rng = ws.Range(ws.Cells(r0, barCol), ws.Cells(r1, barCol))
    For Each s In ws.Shapes
        If Left$(s.Name, 4) = "RXP_" Then
            If Not Intersect(s.TopLeftCell, rng) Is Nothing Then s.Delete
        End If
    Next s
End Sub

Public Sub LimparTodasAsBarras()
    Dim ws As Worksheet, s As Shape, i As Long
    For Each ws In ThisWorkbook.Worksheets
        For i = ws.Shapes.Count To 1 Step -1
            If Left$(ws.Shapes(i).Name, 4) = "RXP_" Then ws.Shapes(i).Delete
        Next i
    Next ws
End Sub

'===============================================================================
'  Utilitarios
'===============================================================================
Private Function EhNumero(v As Variant) As Boolean
    EhNumero = False
    If IsError(v) Then Exit Function
    If IsNumeric(v) Then EhNumero = True
End Function

Private Function ConfirmarBloomberg() As Boolean
    Dim d As Variant
    d = ThisWorkbook.Worksheets("Painel").Range("C4").Value
    If Not IsDate(d) Then
        MsgBox "Preencha a data de fechamento em Painel!C4.", vbExclamation, "Raio-XP"
        ConfirmarBloomberg = False
        Exit Function
    End If
    ConfirmarBloomberg = True
End Function

Private Sub RestaurarApp(ByVal calcMode As XlCalculation)
    Application.Calculation = calcMode
    Application.EnableEvents = True
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    Application.CutCopyMode = False
End Sub
