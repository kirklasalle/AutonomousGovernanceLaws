<#
.SYNOPSIS
    Install the AGL constitutional charter into a target project, byte-for-byte, and verify it.

.DESCRIPTION
    Copies Permanent_Active_Directives.txt, AGENTIC_PRIME_DIRECTIVE.md,
    AGENTIC_SACRED_COVENANT.md and config\charter_manifest.json from this repository
    into -Target, then recomputes each charter digest exactly as GovernanceKernel does
    (SHA-256 over the bytes with CRLF normalised to LF) and compares it with the manifest.

    GovernanceKernel refuses to boot unless all four files are present and byte-identical
    (apart from CRLF/LF). Do not move them with Get-Content | Set-Content, an editor
    "save", or text copied from rendered Markdown: an added BOM, a trailing newline, a
    changed dash or stripped ** markers all break the pinned hashes.

    See documents/INSTALLATION_METHODS_REPORT.md for the analysis behind this procedure.

.PARAMETER Target
    Root directory of the project that will run GovernanceKernel / agy-governance.
    Pass its manifest to the kernel; charter paths resolve relative to that manifest.
    Default ledger and halt paths still use the working directory.

.PARAMETER Force
    Overwrite charter files that already exist in -Target but do not match the manifest.

.PARAMETER VerifyOnly
    Do not copy anything; only verify the charter already present in -Target.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install_charter.ps1 -Target D:\Projects\MyAgent

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install_charter.ps1 -Target D:\Projects\MyAgent -VerifyOnly
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [switch]$Force,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$Source = Split-Path -Parent $PSScriptRoot
$ManifestRel = 'config\charter_manifest.json'

function Get-CharterHash {
    param([string]$Path)
    # Mirrors GovernanceKernel._compute_sha256: read bytes, replace CRLF with LF, SHA-256.
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $buffer = New-Object System.IO.MemoryStream
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i] -eq 13 -and ($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10) { continue }
        $buffer.WriteByte($bytes[$i])
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $digest = $sha.ComputeHash($buffer.ToArray())
    } finally {
        $sha.Dispose()
    }
    return -join ($digest | ForEach-Object { $_.ToString('x2') })
}

function Test-SafeRelativePath {
    param([string]$Rel)
    if ([string]::IsNullOrWhiteSpace($Rel)) { return $false }
    $norm = $Rel -replace '\\', '/'
    if ($norm.StartsWith('/') -or $norm -match '^[A-Za-z]:') { return $false }
    $parts = $norm.Split('/')
    if ($parts -contains '..' -or $parts -contains '') { return $false }
    return $true
}

function Read-CharterManifest {
    param([string]$Root)
    $path = Join-Path $Root $ManifestRel
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Charter manifest not found: $path"
    }
    $m = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    if ($null -eq $m.charter_files -or @($m.charter_files.PSObject.Properties).Count -eq 0) {
        throw "Charter manifest lists no charter files: $path"
    }
    if ($m.algorithm -and ([string]$m.algorithm).ToUpperInvariant() -ne 'SHA-256') {
        throw "Unsupported charter hash algorithm: $($m.algorithm)"
    }
    foreach ($entry in $m.charter_files.PSObject.Properties) {
        if (-not (Test-SafeRelativePath $entry.Name)) {
            throw "Unsafe charter entry path in manifest: $($entry.Name)"
        }
    }
    return $m
}

function Test-Charter {
    param([string]$Root, $Manifest)
    $results = @()
    foreach ($entry in $Manifest.charter_files.PSObject.Properties) {
        if (-not (Test-SafeRelativePath $entry.Name)) {
            throw "Unsafe charter entry path in manifest: $($entry.Name)"
        }
        $path = Join-Path $Root $entry.Name
        $expected = ([string]$entry.Value).ToLowerInvariant()
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            $results += [pscustomobject]@{ File = $entry.Name; Status = 'MISSING'; Expected = $expected.Substring(0, 16); Actual = '' }
            continue
        }
        $actual = Get-CharterHash -Path $path
        $status = if ($actual -eq $expected) { 'OK' } else { 'MISMATCH' }
        $results += [pscustomobject]@{ File = $entry.Name; Status = $status; Expected = $expected.Substring(0, 16); Actual = $actual.Substring(0, 16) }
    }
    return $results
}

if (-not (Test-Path -LiteralPath $Target -PathType Container)) {
    throw "Target directory does not exist: $Target"
}
$Target = (Resolve-Path -LiteralPath $Target).Path

if (-not $VerifyOnly) {
    $sourceManifest = Read-CharterManifest -Root $Source
    $sourceCheck = Test-Charter -Root $Source -Manifest $sourceManifest
    if ($sourceCheck | Where-Object { $_.Status -ne 'OK' }) {
        $sourceCheck | Format-Table -AutoSize | Out-String | Write-Host
        throw "Source charter in $Source does not match its own manifest. Run scripts\verify_charter.py and restore the files from git before installing."
    }

    $files = @($sourceManifest.charter_files.PSObject.Properties | ForEach-Object { $_.Name }) + $ManifestRel
    $plan = @()
    foreach ($rel in $files) {
        $src = Join-Path $Source $rel
        $dst = Join-Path $Target $rel
        $action = 'copy'
        if (Test-Path -LiteralPath $dst -PathType Leaf) {
            $same = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
            if (-not $same -and $rel -ne $ManifestRel) {
                $expected = ([string]$sourceManifest.charter_files.$rel).ToLowerInvariant()
                $same = (Get-CharterHash -Path $dst) -eq $expected
            }
            if ($same) {
                $action = 'present'
            } elseif ($Force) {
                $action = 'copy'
            } else {
                throw "$dst already exists and differs from the pinned charter. Re-run with -Force to replace it."
            }
        }
        $plan += [pscustomobject]@{ Rel = $rel; Src = $src; Dst = $dst; Action = $action }
    }
    foreach ($item in $plan) {
        if ($item.Action -eq 'present') {
            Write-Host "  present   $($item.Rel)"
            continue
        }
        $dstDir = Split-Path -Parent $item.Dst
        if (-not (Test-Path -LiteralPath $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir | Out-Null
        }
        Copy-Item -LiteralPath $item.Src -Destination $item.Dst -Force
        Write-Host "  copied    $($item.Rel)"
    }
}

$targetManifest = Read-CharterManifest -Root $Target
$results = Test-Charter -Root $Target -Manifest $targetManifest
$results | Format-Table -AutoSize | Out-String | Write-Host

if ($results | Where-Object { $_.Status -ne 'OK' }) {
    Write-Host "CHARTER INVALID in $Target. GovernanceKernel will refuse to boot." -ForegroundColor Red
    exit 1
}

Write-Host ("CHARTER VERIFIED in {0} (manifest v{1}, {2} files)." -f $Target, $targetManifest.version, $results.Count) -ForegroundColor Green
Write-Host "Verify with: agy-governance --manifest `"$Target\$ManifestRel`" verify"
exit 0
