<#
.SYNOPSIS
  Starts Manor Lords through Steam. Can wait until HarnessBoot has loaded the test save.
.DESCRIPTION
  NOTE: harness\run.py is the normal way to run the game for a test. This script is for manual use only.
  It starts the game through Steam, so it cannot pass per-run settings to the game.
  1. Refuses to start if the game is already running. Run game-close.ps1 first.
  2. Deletes the old boot.json and ready.marker, so an old result is never read as a new one.
  3. Starts the game with the Steam URL steam://rungameid/<AppId>.
  4. Waits for the game process to appear.
  5. With -WaitForBoot: waits until HarnessBoot writes boot.json with state READY or FAILED.

  HarnessBoot must be turned on. Steam starts the game, so the script cannot pass environment
  variables to it. Use the switch file ue4ss\harness\autoboot.enable (see harness\README.md).
  The script does not touch save files.
.PARAMETER GameDir
  Manor Lords install folder (the folder that contains ManorLords\).
.PARAMETER AppId
  Steam app ID. Default 1363080 (Manor Lords).
.PARAMETER StartTimeoutSeconds
  How long to wait for the game process. Default 120.
.PARAMETER WaitForBoot
  Wait for HarnessBoot to finish.
.PARAMETER BootTimeoutSeconds
  How long to wait for HarnessBoot, counted from the process start. Default 300.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\game-launch.ps1 -WaitForBoot
.NOTES
  Exit codes: 0 = started (and READY if -WaitForBoot), 1 = already running or HarnessBoot is off,
  2 = the process did not start, 3 = HarnessBoot ended in FAILED, 4 = timeout while waiting for HarnessBoot,
  5 = other error.
#>
[CmdletBinding()]
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Manor Lords',
    [string]$AppId = '1363080',
    [int]$StartTimeoutSeconds = 120,
    [switch]$WaitForBoot,
    [int]$BootTimeoutSeconds = 300
)
$ErrorActionPreference = 'Stop'

$ue4ssDir   = Join-Path $GameDir 'ManorLords\Binaries\Win64\ue4ss'
$harnessDir = Join-Path $ue4ssDir 'harness'
$bootFile   = Join-Path $harnessDir 'boot.json'
$readyFile  = Join-Path $harnessDir 'ready.marker'
$switchFile = Join-Path $harnessDir 'autoboot.enable'

function Get-ShippingProcess {
    Get-Process -Name 'ManorLords-Win64-Shipping' -ErrorAction SilentlyContinue | Select-Object -First 1
}

try {
    if (Get-ShippingProcess) {
        Write-Host 'launch: the game is already running. Run harness\game-close.ps1 first.'
        exit 1
    }
    if ($WaitForBoot -and -not (Test-Path -LiteralPath $switchFile)) {
        Write-Host "launch: HarnessBoot is off (missing $switchFile). Create it to use -WaitForBoot."
        exit 1
    }

    foreach ($stale in @($bootFile, $readyFile)) {
        if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
    }

    Write-Host "launch: starting steam://rungameid/$AppId"
    Start-Process "steam://rungameid/$AppId"

    $deadline = (Get-Date).AddSeconds($StartTimeoutSeconds)
    $proc = $null
    while ((Get-Date) -lt $deadline -and -not $proc) {
        Start-Sleep -Milliseconds 500
        $proc = Get-ShippingProcess
    }
    if (-not $proc) {
        Write-Host "launch: ERROR: the game process did not appear in $StartTimeoutSeconds s"
        exit 2
    }
    $startedAt = Get-Date
    Write-Host ('launch: game process is up (PID {0})' -f $proc.Id)

    if (-not $WaitForBoot) { exit 0 }

    $deadline = $startedAt.AddSeconds($BootTimeoutSeconds)
    $lastState = ''
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
        if (-not (Get-ShippingProcess)) {
            Write-Host 'launch: ERROR: the game process ended while waiting for HarnessBoot'
            exit 3
        }
        if (-not (Test-Path -LiteralPath $bootFile)) { continue }
        # The mod writes the file atomically, but read it defensively.
        try { $boot = Get-Content -LiteralPath $bootFile -Raw | ConvertFrom-Json } catch { continue }
        if ($boot.state -ne $lastState) {
            Write-Host ('launch: HarnessBoot state {0}' -f $boot.state)
            $lastState = $boot.state
        }
        if ($boot.state -eq 'READY') {
            Write-Host ('launch: READY after {0:N0} s' -f ((Get-Date) - $startedAt).TotalSeconds)
            exit 0
        }
        if ($boot.state -eq 'FAILED') {
            Write-Host ('launch: HarnessBoot FAILED: {0}' -f $boot.reason)
            exit 3
        }
    }
    Write-Host "launch: timeout: HarnessBoot did not finish in $BootTimeoutSeconds s (last state: $lastState)"
    exit 4
} catch {
    Write-Host "launch: ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 5
}
