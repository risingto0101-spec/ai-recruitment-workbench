' DeepSeek Key 配置工具（VBS 图形界面版）
' 解决部分 Windows 上 bat 窗口闪退的问题

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

thisDir = fso.GetParentFolderName(WScript.ScriptFullName)
envFile = fso.BuildPath(thisDir, ".env")

key = InputBox("Enter your DeepSeek API Key below." & vbCrLf & vbCrLf & "Leave blank to use rule engine (no AI)." & vbCrLf & vbCrLf & "Get key: platform.deepseek.com/api_keys", "AI Recruit - DeepSeek Key")

If IsEmpty(key) Then
    WScript.Quit 0
End If

If key = "" Then
    aiEnabled = "false"
    savedKey = ""
    msg = "Key is empty. AI disabled, rule engine will be used."
Else
    aiEnabled = "true"
    savedKey = key
    msg = "DeepSeek Key saved. AI enabled."
End If

Set file = fso.CreateTextFile(envFile, True)
file.WriteLine "# DeepSeek AI config (leave empty to use rule engine)"
file.WriteLine "DEEPSEEK_API_KEY=" & savedKey
file.WriteLine "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1"
file.WriteLine "AI_ENABLED=" & aiEnabled
file.WriteLine ""
file.WriteLine "# Server config"
file.WriteLine "HOST=127.0.0.1"
file.WriteLine "PORT=8000"
file.WriteLine ""
file.WriteLine "# Database path"
file.WriteLine "DB_PATH=recruitment.db"
file.Close

MsgBox msg & vbCrLf & vbCrLf & "Config file: " & envFile, vbInformation, "Done"
