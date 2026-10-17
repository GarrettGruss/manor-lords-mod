<#
.SYNOPSIS
  Disables or removes the harness in a Manor Lords UE4SS install.
.DESCRIPTION
  Both modes first restore the user's settings files that install.ps1 backed up (spec 11), and check their
  SHA-256. They refuse this while the game runs, because the game writes its settings when it exits.

  Default mode (disable). Keeps all files, so it is reversible.
    - Deletes the switch file ue4ss\harness\autoboot.enable.
    - Sets every harness mod to "Name : 0" in Mods\mods.txt.
    To enable again, run deploy.ps1.

  -Remove mode (full uninstall of what deploy.ps1 installed).
    - Does everything from the default mode.
    - Deletes the files listed in Mods\.harness-manifest.json and prunes empty folders.
    - Removes the harness mod lines from mods.txt.
    - Deletes the manifest.
    - Deletes the asset mod paks that pakmod.py installed (spec 09): only files listed in
      ManorLords\Content\Paks\~mods\.harness-paks.json whose SHA-256 still matches, only inside ~mods.
      It deletes the pak manifest, and the ~mods folder if the harness created it and it is empty.
      A pak that changed since install is skipped with a warning.
    - Deletes the folders ue4ss\bridge and ue4ss\harness (only these two).
    - Deletes the slot folders that install.ps1 built (slots\<n>). Junctions are removed as links first.
    - Keeps mods.txt.harness.bak. The script prints its path, so you can restore it by hand.

  Harness mods are the top-level folders in the manifest, except "shared".
  Stock UE4SS mods, UE4SS itself, dwmapi.dll, UE4SS-settings.ini and the game saves are never touched.
  The script refuses to run when a path to change is outside -GameDir.
  Running the script twice is safe. The second run finds nothing to do.

  To turn UE4SS off for one launch only, add the Steam launch option --disable-ue4ss.
  To turn UE4SS off fully, rename dwmapi.dll. This script does neither.
.PARAMETER GameDir
  Manor Lords install dir (the folder containing ManorLords\).
.PARAMETER DryRun
  Report what would happen; change nothing.
.PARAMETER Remove
  Full uninstall instead of disable.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1 -DryRun
  Shows what the disable mode would do.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1
  Disables the harness. Run deploy.ps1 to enable it again.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\uninstall.ps1 -Remove -GameDir 'D:\Games\Manor Lords'
  Removes everything deploy.ps1 installed.
#>
[CmdletBinding()]
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Manor Lords',
    [switch]$DryRun,
    [switch]$Remove,
    [string]$SlotsDir = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'installstate.ps1')
# $PSScriptRoot is empty in parameter defaults on PowerShell 5.1, so the default is set here.
if (-not $SlotsDir) { $SlotsDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'slots' }

$modsDir      = Join-Path $GameDir 'ManorLords\Binaries\Win64\ue4ss\Mods'
$ue4ssDir     = Split-Path -Parent $modsDir
$modsTxt      = Join-Path $modsDir 'mods.txt'
$bakPath      = "$modsTxt.harness.bak"
$manifestPath = Join-Path $modsDir '.harness-manifest.json'
$switchPath   = Join-Path $ue4ssDir 'harness\autoboot.enable'
$pakModsDir   = Join-Path $GameDir 'ManorLords\Content\Paks\~mods'
$pakManifest  = Join-Path $pakModsDir '.harness-paks.json'
$outputDirs   = @((Join-Path $ue4ssDir 'bridge'), (Join-Path $ue4ssDir 'harness'))
$tag = if ($DryRun) { '[dry-run] ' } else { '' }

$deleted = 0; $disabled = 0; $linesRemoved = 0; $errors = 0

function Test-InsideGameDir([string]$path) {
    $root = [IO.Path]::GetFullPath($GameDir).TrimEnd('\') + '\'
    $full = [IO.Path]::GetFullPath($path)
    return $full.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-InsideGameDir([string]$path) {
    if (-not (Test-InsideGameDir $path)) { throw "Refusing to touch a path outside GameDir: $path" }
}

function Read-ManifestFiles {
    $files = @()
    if (-not (Test-Path -LiteralPath $manifestPath)) { return $files }
    $m = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    foreach ($p in $m.files.PSObject.Properties) { $files += $p.Name }
    return $files
}

function Get-HarnessModNames([string[]]$manifestFiles) {
    $names = New-Object System.Collections.Generic.List[string]
    foreach ($rel in $manifestFiles) {
        $top = $rel.Split('\')[0]
        if ($top -ine 'shared' -and -not $names.Contains($top)) { $names.Add($top) }
    }
    return $names
}

function Remove-ManifestFiles([string[]]$manifestFiles) {
    foreach ($rel in $manifestFiles) {
        $dst = Join-Path $modsDir $rel
        Assert-InsideGameDir $dst
        # A manifest entry such as "..\..\x" must never reach a file outside the Mods folder.
        $modsRoot = [IO.Path]::GetFullPath($modsDir).TrimEnd('\') + '\'
        if (-not [IO.Path]::GetFullPath($dst).StartsWith($modsRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to delete a file outside the Mods folder: $rel"
        }
        if (-not (Test-Path -LiteralPath $dst)) { continue }
        Write-Host ("{0}deleted    Mods\{1}" -f $tag, $rel)
        $script:deleted++
        if ($DryRun) { continue }
        Remove-Item -LiteralPath $dst -Force
        # Prune empty parent folders. Never Mods itself.
        $d = Split-Path -Parent $dst
        while ($d -and ($d.TrimEnd('\') -ine $modsDir.TrimEnd('\')) -and (Test-Path -LiteralPath $d) -and -not (Get-ChildItem -LiteralPath $d -Force)) {
            Remove-Item -LiteralPath $d -Force
            $d = Split-Path -Parent $d
        }
    }
}

# Spec 09: delete only the paks that pakmod.py recorded, and only if they are unchanged.
function Remove-HarnessPaks {
    if (-not (Test-Path -LiteralPath $pakManifest)) { return }
    Assert-InsideGameDir $pakManifest
    $m = Get-Content -LiteralPath $pakManifest -Raw | ConvertFrom-Json
    $kept = 0
    foreach ($p in $m.files.PSObject.Properties) {
        $name = $p.Name
        if ($name -ne (Split-Path -Leaf $name) -or $name -notlike '*.pak') { throw "Pak manifest entry is not a plain pak file name: $name" }
        $dst = Join-Path $pakModsDir $name
        Assert-InsideGameDir $dst
        if (-not (Test-Path -LiteralPath $dst)) { continue }
        if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ine $p.Value) {
            Write-Warning "pak changed since install, not deleted: $name"
            $kept++
            continue
        }
        Write-Host ("{0}deleted    ~mods\{1}" -f $tag, $name)
        $script:deleted++
        if (-not $DryRun) { Remove-Item -LiteralPath $dst -Force }
    }
    if ($kept -gt 0) { Write-Host 'paks       manifest kept because a pak was skipped'; return }
    Write-Host ("{0}deleted    ~mods\.harness-paks.json" -f $tag)
    $script:deleted++
    if ($DryRun) { return }
    Remove-Item -LiteralPath $pakManifest -Force
    $isEmpty = -not (Get-ChildItem -LiteralPath $pakModsDir -Force)
    if ($m.created_dir -eq $true -and $isEmpty) { Remove-Item -LiteralPath $pakModsDir -Force; Write-Host 'deleted    empty ~mods folder' }
}

function Remove-SwitchFile {
    Assert-InsideGameDir $switchPath
    if (-not (Test-Path -LiteralPath $switchPath)) { Write-Host 'autoboot  switch file not present'; return }
    Write-Host ("{0}deleted    ue4ss\harness\autoboot.enable" -f $tag)
    $script:deleted++
    if (-not $DryRun) { Remove-Item -LiteralPath $switchPath -Force }
}

function Remove-OutputFolders {
    foreach ($dir in $outputDirs) {
        Assert-InsideGameDir $dir
        if (-not (Test-Path -LiteralPath $dir)) { continue }
        $count = @(Get-ChildItem -LiteralPath $dir -Recurse -File -Force).Count
        Write-Host ("{0}deleted    folder ue4ss\{1} ({2} files)" -f $tag, (Split-Path -Leaf $dir), $count)
        $script:deleted++
        if (-not $DryRun) { Remove-Item -LiteralPath $dir -Recurse -Force }
    }
}

# Disable mode sets "Name : 0". Remove mode deletes the line. Order and other lines stay as they are.
function Update-ModsTxt([System.Collections.Generic.List[string]]$names) {
    if (-not (Test-Path -LiteralPath $modsTxt)) { Write-Host 'mods.txt   not found, nothing to do'; return }
    $raw = [IO.File]::ReadAllText($modsTxt)
    $eol = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
    $endsNl = $raw.EndsWith("`n")
    $body = if ($endsNl) { $raw.Substring(0, $raw.Length - $eol.Length) } else { $raw }
    $lines = New-Object System.Collections.Generic.List[string]
    if ($body.Length -gt 0) { $lines.AddRange([string[]]($body -split "\r?\n")) }
    $changes = @()

    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        if ($lines[$i] -notmatch '^\s*([^;\s:][^:]*?)\s*:\s*(\d+)\s*$') { continue }
        $name = $Matches[1]; $value = $Matches[2]
        if (-not ($names | Where-Object { $_ -ieq $name })) { continue }
        if ($Remove) {
            $lines.RemoveAt($i); $changes += "removed $name"; $script:linesRemoved++
        } elseif ($value -ne '0') {
            $lines[$i] = "$name : 0"; $changes += "disabled $name"; $script:disabled++
        }
    }
    if ($changes.Count -eq 0) { Write-Host 'mods.txt   unchanged'; return }
    Write-Host ("{0}mods.txt   {1}" -f $tag, ($changes -join ', '))
    if ($DryRun) { return }
    if (-not (Test-Path -LiteralPath $bakPath)) {
        Copy-Item -LiteralPath $modsTxt -Destination $bakPath
        Write-Host 'mods.txt   backup written: mods.txt.harness.bak'
    }
    $out = ($lines -join $eol); if ($endsNl) { $out += $eol }
    [IO.File]::WriteAllText($modsTxt, $out, (New-Object Text.UTF8Encoding($false)))
}

function Remove-Manifest {
    if (-not (Test-Path -LiteralPath $manifestPath)) { return }
    Assert-InsideGameDir $manifestPath
    Write-Host ("{0}deleted    Mods\.harness-manifest.json" -f $tag)
    $script:deleted++
    if (-not $DryRun) { Remove-Item -LiteralPath $manifestPath -Force }
}

# Spec 11: slots that install.ps1 built. The state lists each junction, so none is deleted through.
function Remove-InstalledSlots {
    $entries = @(Read-SlotsState $SlotsDir)
    if ($entries.Count -eq 0) { return }
    foreach ($entry in $entries) {
        Write-Host ("{0}deleted    slot {1}" -f $tag, $entry.slot)
        $script:deleted++
        if (-not $DryRun) { Remove-Slot $SlotsDir $entry }
    }
    if (-not $DryRun) { Remove-Item -LiteralPath (Get-SlotsStatePath $SlotsDir) -Force }
}

# ---- Checks ----
if (-not (Test-Path -LiteralPath $modsDir)) { throw "UE4SS Mods dir not found: $modsDir" }
foreach ($p in @($modsDir, $modsTxt, $manifestPath, $switchPath, $pakModsDir, $pakManifest) + $outputDirs) { Assert-InsideGameDir $p }

if (Get-Process -Name 'ManorLords-Win64-Shipping' -ErrorAction SilentlyContinue) {
    Write-Warning 'Game is running (ManorLords-Win64-Shipping.exe). Changes take effect at the next game start.'
}

# ---- Work ----
# The settings come first: they are the user's data, and they do not depend on the game folder.
try {
    if ($DryRun) {
        if (Test-Path -LiteralPath (Get-SettingsStatePath $SlotsDir)) { Write-Host '[dry-run] settings   would restore the install backup' }
    } else {
        if (Test-Path -LiteralPath (Get-SettingsStatePath $SlotsDir)) { Assert-GameNotRunning }
        $restored = Restore-UserFiles $SlotsDir
        $deleted += $restored
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $errors++
}

try {
    $manifestFiles = @(Read-ManifestFiles)
    $modNames = Get-HarnessModNames $manifestFiles
    if ($manifestFiles.Count -eq 0) { Write-Host 'manifest   not found or empty: no harness mods are known' }

    Remove-SwitchFile
    if ($Remove) { Remove-ManifestFiles $manifestFiles }
    Update-ModsTxt $modNames
    if ($Remove) {
        Remove-Manifest
        Remove-HarnessPaks
        Remove-OutputFolders
        Remove-InstalledSlots
        if (Test-Path -LiteralPath $bakPath) { Write-Host "backup     kept, restore by hand if needed: $bakPath" }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $errors++
}

$total = $deleted + $disabled + $linesRemoved
if ($errors -eq 0 -and $total -eq 0) { Write-Host 'Nothing to do.' }
Write-Host ("{0}Summary: {1} deleted, {2} mods disabled, {3} mods.txt lines removed, errors: {4}" -f $tag, $deleted, $disabled, $linesRemoved, $errors)
if ($errors -gt 0) { exit 1 }
exit 0
