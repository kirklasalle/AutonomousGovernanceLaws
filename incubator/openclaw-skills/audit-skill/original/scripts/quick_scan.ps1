# quick_scan.ps1 - Non-destructive quick system scan
$reportPath = "G:\Users\kirkl\.openclaw\workspace\logs\audit-skill\quick_$(Get-Date -Format yyyy-MM-dd_HH-mm).log"
New-Item -ItemType Directory -Path (Split-Path $reportPath) -Force | Out-Null
$out = @()
$out += "## Quick Scan - $(Get-Date -Format u)"
$out += "--- Systeminfo ---"
$out += (systeminfo)
$out += "--- Disk ---"
$out += (Get-PSDrive -PSProvider FileSystem | Select-Object Name,Free,Used)
$out += "--- Memory ---"
$out += (Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize)
$out += "--- Netstat ---"
$out += (netstat -an)
$out | Out-File -FilePath $reportPath -Encoding utf8
Write-Output $reportPath
