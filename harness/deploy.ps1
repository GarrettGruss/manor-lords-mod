<#
.SYNOPSIS
  Deploys repo mods (mod\) into a Manor Lords UE4SS install. Copies files, verifies SHA256.
.PARAMETER GameDir
  Manor Lords install dir (the folder containing ManorLords\).
.PARAMETER DryRun
  Report what would happen; change nothing.
.PARAMETER Clean
  Remove previously harness-deployed files (per manifest) that no longer exist in mod\.
.PARAMETER NoPak
  Do not install mod paks (mod\<Name>\paks\<Name>_P.pak) into Content\Paks\~mods.
#>
[CmdletBinding()]
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Manor Lords',
    [switch]$DryRun,
    [switch]$Clean,
    [switch]$NoPak
)
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$modSrc   = Join-Path $repoRoot 'mod'
$modsDir  = Join-Path $GameDir 'ManorLords\Binaries\Win64\ue4ss\Mods'
$modsTxt  = Join-Path $modsDir 'mods.txt'
$bakPath  = "$modsTxt.harness.bak"
$manifestPath = Join-Path $modsDir '.harness-manifest.json'
$tag = if ($DryRun) { '[dry-run] ' } else { '' }

if (-not (Test-Path -LiteralPath $modSrc))  { throw "Repo mod dir not found: $modSrc" }
if (-not (Test-Path -LiteralPath $modsDir)) { throw "UE4SS Mods dir not found: $modsDir" }
if (-not (Test-Path -LiteralPath $modsTxt)) { throw "mods.txt not found: $modsTxt" }

if (Get-Process -Name 'ManorLords-Win64-Shipping' -ErrorAction SilentlyContinue) {
    Write-Warning 'Game is running (ManorLords-Win64-Shipping.exe). Continuing; UE4SS can hot reload.'
}

function Get-RelPath([string]$base, [string]$full) {
    $b = $base.TrimEnd('\') + '\'
    return $full.Substring($b.Length)
}

# ---- Build desired file set: key = path relative to Mods (backslashes) ----
$desired = [ordered]@{}   # rel -> source full path
$mods = New-Object System.Collections.Generic.List[string]
foreach ($top in Get-ChildItem -LiteralPath $modSrc -Directory | Sort-Object Name) {
    $isShared = ($top.Name -ieq 'shared')
    if (-not $isShared) { $mods.Add($top.Name) }
    foreach ($f in Get-ChildItem -LiteralPath $top.FullName -Recurse -File) {
        $inner = Get-RelPath $top.FullName $f.FullName
        # Source folders of a mod (pak, UE project, art) are not Lua; the game does not need them.
        if (-not $isShared -and ($inner.Split('\')[0] -in @('paks', 'ue', 'art'))) { continue }
        $rel = Join-Path $top.Name $inner
        $desired[$rel] = $f.FullName
    }
}

# ---- Load previous manifest ----
$prev = @{}   # rel -> sha
if (Test-Path -LiteralPath $manifestPath) {
    $m = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    foreach ($p in $m.files.PSObject.Properties) { $prev[$p.Name] = $p.Value }
}

$copied = 0; $unchanged = 0; $removed = 0; $errors = 0
$newManifest = [ordered]@{}

# ---- Copy ----
foreach ($rel in $desired.Keys) {
    $src = $desired[$rel]
    $dst = Join-Path $modsDir $rel
    $srcHash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
    $dstHash = $null
    if (Test-Path -LiteralPath $dst) { $dstHash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash }
    if ($dstHash -eq $srcHash) {
        Write-Host ("unchanged  {0}" -f $rel)
        $unchanged++
    } else {
        Write-Host ("{0}copied     {1}" -f $tag, $rel)
        if (-not $DryRun) {
            $dir = Split-Path -Parent $dst
            if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dst -Force
        }
        $copied++
    }
    $newManifest[$rel] = $srcHash
}

# ---- Stale (in manifest, not in repo) ----
$removedMods = New-Object System.Collections.Generic.List[string]
foreach ($rel in @($prev.Keys)) {
    if ($desired.Contains($rel)) { continue }
    if ($Clean) {
        $dst = Join-Path $modsDir $rel
        if (Test-Path -LiteralPath $dst) {
            Write-Host ("{0}removed    {1}" -f $tag, $rel)
            if (-not $DryRun) { Remove-Item -LiteralPath $dst -Force }
            $removed++
        }
        $top = $rel.Split('\')[0]
        if ($top -ine 'shared' -and -not $removedMods.Contains($top) -and -not $mods.Contains($top)) { $removedMods.Add($top) }
        if (-not $DryRun) {
            # prune empty parent dirs (never Mods itself)
            $d = Split-Path -Parent $dst
            while ($d -and ($d.TrimEnd('\') -ine $modsDir.TrimEnd('\')) -and (Test-Path -LiteralPath $d) -and -not (Get-ChildItem -LiteralPath $d -Force)) {
                Remove-Item -LiteralPath $d -Force
                $d = Split-Path -Parent $d
            }
        }
    } else {
        Write-Host ("stale      {0}  (not in repo; use -Clean to remove)" -f $rel)
        $newManifest[$rel] = $prev[$rel]
    }
}

# ---- Verify ----
$verified = 0
if (-not $DryRun) {
    foreach ($rel in $desired.Keys) {
        $dst = Join-Path $modsDir $rel
        $h = $null
        if (Test-Path -LiteralPath $dst) { $h = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash }
        if ($h -ne $newManifest[$rel]) { Write-Host "VERIFY FAILED: $rel" -ForegroundColor Red; $errors++ } else { $verified++ }
    }
}

# ---- mods.txt ----
function Update-ModsTxt {
    $raw = [IO.File]::ReadAllText($modsTxt)
    $eol = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
    $endsNl = $raw.EndsWith("`n")
    $body = if ($endsNl) { $raw.Substring(0, $raw.Length - $eol.Length) } else { $raw }
    $lines = New-Object System.Collections.Generic.List[string]
    if ($body.Length -gt 0) { $lines.AddRange([string[]]($body -split "\r?\n")) }
    $changes = @()

    foreach ($name in $mods) {
        $idx = -1; $val = $null
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match '^\s*([^;\s:][^:]*?)\s*:\s*(\d+)\s*$' -and $Matches[1] -ieq $name) { $idx = $i; $val = $Matches[2]; break }
        }
        if ($idx -ge 0) {
            if ($val -ne '1') { $lines[$idx] = "$name : 1"; $changes += "enabled $name" }
            continue
        }
        # insert before the keybinds comment block, after last non-blank line above it
        $kb = -1
        for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^\s*;\s*Built-in keybinds') { $kb = $i; break } }
        if ($kb -lt 0) { for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^\s*Keybinds\s*:') { $kb = $i; break } } }
        if ($kb -lt 0) { $kb = $lines.Count }
        $at = $kb
        while ($at -gt 0 -and [string]::IsNullOrWhiteSpace($lines[$at - 1])) { $at-- }
        $lines.Insert($at, "$name : 1")
        $changes += "added $name"
    }
    foreach ($name in $removedMods) {
        for ($i = $lines.Count - 1; $i -ge 0; $i--) {
            if ($lines[$i] -match '^\s*([^;\s:][^:]*?)\s*:\s*\d+\s*$' -and $Matches[1] -ieq $name) { $lines.RemoveAt($i); $changes += "removed $name" }
        }
    }
    if ($changes.Count -eq 0) { Write-Host 'mods.txt   unchanged'; return 0 }
    Write-Host ("{0}mods.txt   {1}" -f $tag, ($changes -join ', '))
    if (-not $DryRun) {
        if (-not (Test-Path -LiteralPath $bakPath)) {
            Copy-Item -LiteralPath $modsTxt -Destination $bakPath
            Write-Host 'mods.txt   backup written: mods.txt.harness.bak'
        }
        $out = ($lines -join $eol); if ($endsNl) { $out += $eol }
        [IO.File]::WriteAllText($modsTxt, $out, (New-Object Text.UTF8Encoding($false)))
    }
    return $changes.Count
}
$txtChanges = Update-ModsTxt | Select-Object -Last 1

# ---- Manifest ----
if (-not $DryRun -and $errors -eq 0) {
    $obj = [ordered]@{ version = 1; files = $newManifest }
    $json = $obj | ConvertTo-Json -Depth 5
    $old = $null; if (Test-Path -LiteralPath $manifestPath) { $old = Get-Content -LiteralPath $manifestPath -Raw }
    if ($old -ne $json) { [IO.File]::WriteAllText($manifestPath, $json, (New-Object Text.UTF8Encoding($false))) }
}

# ---- Mod paks ----
# A mod's own pak is mod\<Name>\paks\<Name>_P.pak. Other paks in that folder are test paks for run.py --pak.
# The pak is listed in the run.py pak manifest, so a run may replace it and its teardown removes it.
$pakCount = 0
if (-not $NoPak) {
    $pakModsDir = Join-Path $GameDir 'ManorLords\Content\Paks\~mods'
    $pakManifestPath = Join-Path $pakModsDir '.harness-paks.json'
    $pakManifest = [ordered]@{ version = 1; created_dir = $false; files = [ordered]@{} }
    if (Test-Path -LiteralPath $pakManifestPath) {
        $pm = Get-Content -LiteralPath $pakManifestPath -Raw | ConvertFrom-Json
        $pakManifest.created_dir = [bool]$pm.created_dir
        foreach ($p in $pm.files.PSObject.Properties) { $pakManifest.files[$p.Name] = $p.Value }
    }
    foreach ($name in $mods) {
        $src = Join-Path $modSrc "$name\paks\${name}_P.pak"
        if (-not (Test-Path -LiteralPath $src)) { continue }
        $pakName = "${name}_P.pak"
        $dst = Join-Path $pakModsDir $pakName
        if ((Test-Path -LiteralPath $dst) -and -not $pakManifest.files.Contains($pakName)) {
            Write-Host "PAK REFUSED: $dst exists and is not in the harness pak manifest; remove it by hand" -ForegroundColor Red
            $errors++; continue
        }
        $srcHash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
        Write-Host ("{0}pak        {1}" -f $tag, $pakName)
        if (-not $DryRun) {
            if (-not (Test-Path -LiteralPath $pakModsDir)) {
                New-Item -ItemType Directory -Path $pakModsDir -Force | Out-Null
                $pakManifest.created_dir = $true
            }
            Copy-Item -LiteralPath $src -Destination $dst -Force
            if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ne $srcHash) {
                Write-Host "VERIFY FAILED: $pakName" -ForegroundColor Red; $errors++; continue
            }
            $pakManifest.files[$pakName] = $srcHash
            $tmp = "$pakManifestPath.tmp"
            [IO.File]::WriteAllText($tmp, ($pakManifest | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))
            Move-Item -LiteralPath $tmp -Destination $pakManifestPath -Force
        }
        $pakCount++
    }
}

Write-Host ("{0}Summary: {1} copied, {2} unchanged, {3} removed, mods.txt changes: {4}, verified: {5}, paks: {6}, errors: {7}" -f $tag, $copied, $unchanged, $removed, $txtChanges, $verified, $pakCount, $errors)
if ($errors -gt 0) { exit 1 }
exit 0
