<#
.SYNOPSIS
  Puts this PC into the harness state: harness game settings and parallel game slots (spec 11).
.DESCRIPTION
  The game reads and writes its settings in the user's REAL folder (%LOCALAPPDATA%\ManorLords\Saved), so
  a run cannot have private settings. This script:
    1. Backs up GameUserSettings.ini, UserSettings.ini and rtsSettings.sav with SHA-256 into slots\.install\.
       It does this once. A second install keeps the first backup, so the user's own values are never lost.
    2. Writes the harness values (low quality, windowed 1280x720, 30 fps) into the real files. Other keys stay.
    3. Builds the slot folders slots\<n>\Manor Lords\ (slot 0 is the game folder) and deploys the mods to each.
  Run uninstall.ps1 to restore the backup. Play the game yourself only after an uninstall.
.PARAMETER Slots
  How many extra slots to build (default 2: slots 1 and 2, with the game folder as slot 0).
.PARAMETER SettingsOnly
  Back up and write the settings, but build no slots.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\install.ps1
#>
[CmdletBinding()]
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Manor Lords',
    [string]$UserDir = (Join-Path $env:LOCALAPPDATA 'ManorLords\Saved'),
    [string]$SlotsDir = '',
    [ValidateRange(0, 3)][int]$Slots = 2,
    [switch]$SettingsOnly,
    [switch]$SkipDeploy
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'installstate.ps1')
# $PSScriptRoot is empty in parameter defaults on PowerShell 5.1, so the default is set here.
if (-not $SlotsDir) { $SlotsDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'slots' }

try {
    Assert-GameNotRunning
    if (-not (Test-Path -LiteralPath (Join-Path $GameDir 'ManorLords\Binaries\Win64'))) { throw "Game not found: $GameDir" }
    New-Item -ItemType Directory -Force -Path $SlotsDir | Out-Null

    Backup-UserFiles $UserDir $SlotsDir
    Set-HarnessUserSettings $UserDir

    if (-not $SettingsOnly) {
        $entries = [System.Collections.Generic.List[object]]::new()
        foreach ($old in Read-SlotsState $SlotsDir) { $entries.Add($old) }
        for ($slot = 1; $slot -le $Slots; $slot++) {
            $entry = New-Slot $GameDir $SlotsDir $slot
            if ($null -eq $entry) { continue }
            $entries.Add($entry)
            Write-SlotsState $SlotsDir $entries  # after each slot, so a failed install can still be removed
            if (-not $SkipDeploy) {
                & (Join-Path $PSScriptRoot 'deploy.ps1') -GameDir $entry.root 6>&1 | Select-Object -Last 1  # only the summary line
            }
        }
    }
    Write-Host 'Install done. Run uninstall.ps1 to restore your own settings.'
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Run uninstall.ps1 to restore what was changed so far.'
    exit 1
}
