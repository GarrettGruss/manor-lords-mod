<#
.SYNOPSIS
  Starts the game several times in a row and records how each start went.
.DESCRIPTION
  For each run:
    1. Close the game (game-close.ps1).
    2. Start it and wait for HarnessBoot (game-launch.ps1 -WaitForBoot).
    3. Count the pauseGame calls HarnessBoot made (from ue4ss\harness\mod.log).
    4. Wait -SettleSeconds, then read the game clock through the bridge (tools\read_clock.py).
       The run is "paused" only if the clock did not move.
  The results go to runs\launch-series-<time>.json and to the console as a table.
  A failed run is a result. The series goes on with the next run.
  At the end the game is left running (and paused if the last run worked). Use game-close.ps1 to close it.
  The script does not touch save files. It needs: HarnessBoot on (autoboot.enable), the project .venv.
.PARAMETER Runs
  Number of runs. Default 10.
.PARAMETER SettleSeconds
  Seconds to wait after READY before the clock check. Default 5.
.PARAMETER ClockSeconds
  Seconds between the two clock reads. Default 6.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\launch-series.ps1 -Runs 3
#>
[CmdletBinding()]
param(
    [int]$Runs = 10,
    [int]$SettleSeconds = 5,
    [int]$ClockSeconds = 6,
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Manor Lords'
)
$ErrorActionPreference = 'Stop'

$repo      = Split-Path -Parent $PSScriptRoot
$python    = Join-Path $repo '.venv\Scripts\python.exe'
$clockTool = Join-Path $PSScriptRoot 'tools\read_clock.py'
$win64     = Join-Path $GameDir 'ManorLords\Binaries\Win64'
$modLog    = Join-Path $win64 'ue4ss\harness\mod.log'
$bootFile  = Join-Path $win64 'ue4ss\harness\boot.json'

if (-not (Test-Path -LiteralPath $python)) { throw "Project venv not found: $python (see mcp\README.md)" }

$env:PYTHONPATH = Join-Path $repo 'mcp'
$env:UE4SS_BRIDGE_GAME_DIR = $win64

$results = @()
for ($i = 1; $i -le $Runs; $i++) {
    Write-Host ("=== run {0} of {1} ===" -f $i, $Runs)
    $row = [ordered]@{ run = $i; closed = $null; launch = $null; state = $null; reason = $null
                       seconds_to_ready = $null; pause_calls = $null; paused = $null; clock_change = $null; error = $null }
    # Not Get-Date -UFormat %s: in PowerShell 5.1 it returns local time, not UTC.
    $startEpoch = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $started = Get-Date

    & (Join-Path $PSScriptRoot 'game-close.ps1') -GraceSeconds 8
    $row.closed = $LASTEXITCODE

    & (Join-Path $PSScriptRoot 'game-launch.ps1') -GameDir $GameDir -WaitForBoot
    $row.launch = $LASTEXITCODE
    $row.seconds_to_ready = [math]::Round(((Get-Date) - $started).TotalSeconds)

    if (Test-Path -LiteralPath $bootFile) {
        try {
            $boot = Get-Content -LiteralPath $bootFile -Raw | ConvertFrom-Json
            $row.state = $boot.state
            $row.reason = $boot.reason
        } catch { $row.error = 'boot.json unreadable' }
    }

    if (Test-Path -LiteralPath $modLog) {
        # Log lines are "<unix time> <number> <LEVEL> [tag] text".
        $calls = 0
        foreach ($line in (Get-Content -LiteralPath $modLog)) {
            if ($line -match '^(\d+) \d+ \w+ \[HarnessBoot\] .*calling pauseGame' -and [int64]$Matches[1] -ge $startEpoch) { $calls++ }
        }
        $row.pause_calls = $calls
    }

    if ($row.launch -eq 0) {
        Start-Sleep -Seconds $SettleSeconds
        $out = & $python $clockTool $ClockSeconds | Select-Object -Last 1
        try {
            $clock = $out | ConvertFrom-Json
            if ($clock.ok) { $row.paused = $clock.paused; $row.clock_change = $clock.change }
            else { $row.error = $clock.error }
        } catch { $row.error = "clock tool output: $out" }
    }

    $results += [pscustomobject]$row
    Write-Host ("run {0}: launch={1} state={2} ready_after={3}s pause_calls={4} paused={5} clock_change={6}" -f
        $i, $row.launch, $row.state, $row.seconds_to_ready, $row.pause_calls, $row.paused, $row.clock_change)
}

$runsDir = Join-Path $repo 'runs'
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null
$file = Join-Path $runsDir ("launch-series-{0}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $file -Encoding UTF8

Write-Host ''
$results | Format-Table run, launch, state, seconds_to_ready, pause_calls, paused, clock_change, reason -AutoSize | Out-String | Write-Host
$good = @($results | Where-Object { $_.state -eq 'READY' -and $_.paused -eq $true }).Count
Write-Host ("Summary: {0} of {1} runs READY and paused. Results: {2}" -f $good, $Runs, $file)
if ($good -lt $Runs) { exit 1 }
exit 0
