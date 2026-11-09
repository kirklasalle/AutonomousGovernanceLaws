# forensic_scan.ps1 - Extended forensic audit (non-destructive)
# Exports Event Viewer logs (last 72 hours), gateway logs, netstat, scheduled tasks
$timestamp = Get-Date -Format yyyy-MM-dd_HH-mm
$logDir = "G:\Users\kirkl\.openclaw\workspace\logs\audit-skill\forensic_$timestamp"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
# Export Application and System events (last 72 hours) using Get-WinEvent for reliable filtering
$start = (Get-Date).AddHours(-72)
try {
    Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$start} | Format-List -Property * | Out-File "$logDir\Application.txt" -Encoding utf8
} catch {
    "Failed to export Application log: $_" | Out-File "$logDir\Application.txt"
}
try {
    Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$start} | Format-List -Property * | Out-File "$logDir\System.txt" -Encoding utf8
} catch {
    "Failed to export System log: $_" | Out-File "$logDir\System.txt"
}
# Gateway log copy (if exists)
$gwLog = "$env:USERPROFILE\tmp\openclaw\openclaw-$(Get-Date -Format yyyy-MM-dd).log"
if(Test-Path $gwLog){ Copy-Item $gwLog $logDir -Force }
# Netstat and connections
netstat -an > "$logDir\netstat.txt"
# Scheduled tasks
schtasks /query /v /fo LIST > "$logDir\scheduled_tasks.txt"
# List installed programs
Try {
    Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName,DisplayVersion,Publisher | Out-File "$logDir\installed_programs.txt" -Encoding utf8
} Catch {
    "Failed to list installed programs: $_" | Out-File "$logDir\installed_programs.txt"
}
# Compact summary for memory append
$summary = @()
$summary += "## $(Get-Date -Format u) - Forensic scan produced"
$summary += "- Log directory: $logDir"
$summary += "- Application log: Application.txt"
$summary += "- System log: System.txt"
$summary += "- Netstat: netstat.txt"
$summary += "- Scheduled tasks: scheduled_tasks.txt"
$summary += "- Installed programs: installed_programs.txt"
$summary | Out-File "$logDir\summary.txt" -Encoding utf8
# Output location
Write-Output $logDir
