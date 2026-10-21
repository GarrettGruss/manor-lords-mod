<#
.SYNOPSIS
  Closes the Manor Lords game of ONE game slot. Asks the game to close first. Kills it only if it does not close in time.
.DESCRIPTION
  NOTE: harness\run.py is the normal way to run the game for a test. This script is for manual use only.
  The game of a slot is found by its game folder: only processes whose exe is under that folder are touched.
  The games of other slots keep running (parallel slots, spec 11). To close every game, use -All on purpose.
  1. Sends a close request to the game window (like the user clicking the close button).
  2. Waits up to -GraceSeconds for the game to exit.
  3. If it is still running, kills it (unless -NoForce is set).
  A normal close lets UE4SS write its log to disk. A kill can lose the end of UE4SS.log.
  The script does not touch save files.
  You must choose one target: -Slot, -GameRoot or -All. There is no default, so a call never closes a game by accident.
.PARAMETER Slot
  Game slot number. 0 is the Steam install; 1 to 3 are read from slots\.install\slots.json of the main checkout.
.PARAMETER GameRoot
  The game folder (the one that holds ManorLords.exe). Use it instead of -Slot for a game in another place.
.PARAMETER All
  Close the games of every slot. This is the old behavior. Use it only when no other agent runs a game.
.PARAMETER SlotsDir
  The folder with the slots. Default: the slots folder of the main checkout (also from a git worktree).
.PARAMETER GraceSeconds
  How long to wait after the close request. Default 20.
.PARAMETER NoForce
  Never kill the game. Exit with code 1 if it is still running after the wait.
.PARAMETER DryRun
  Only print which processes would be closed. Closes nothing.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\game-close.ps1 -Slot 2
.NOTES
  Exit codes: 0 = closed normally or not running, 1 = killed or still running (see message), 2 = error.
#>
[CmdletBinding()]
param(
    [int]$Slot = -1,
    [string]$GameRoot,
    [switch]$All,
    [string]$SlotsDir,
    [int]$GraceSeconds = 20,
    [switch]$NoForce,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'

# The game process and the launcher stub that starts it.
$names = @('ManorLords-Win64-Shipping', 'ManorLords')

# The main checkout of a git worktree (a worktree has a .git file), or the repo itself.
function Get-MainCheckout([string]$RepoRoot) {
    $gitPath = Join-Path $RepoRoot '.git'
    if (Test-Path -LiteralPath $gitPath -PathType Leaf) {
        $text = (Get-Content -LiteralPath $gitPath -Raw).Trim()
        if ($text -match '^gitdir:\s*(.+)$') {
            $gitDir = $Matches[1].Trim()
            return (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $gitDir)))
        }
    }
    return $RepoRoot
}

function Resolve-SlotRoot([int]$Number) {
    if ($Number -eq 0) {
        return (Join-Path ${env:ProgramFiles(x86)} 'Steam\steamapps\common\Manor Lords')
    }
    $dir = $SlotsDir
    if (-not $dir) { $dir = Join-Path (Get-MainCheckout (Split-Path -Parent $PSScriptRoot)) 'slots' }
    $state = Join-Path $dir '.install\slots.json'
    if (-not (Test-Path -LiteralPath $state)) { throw "slot state file not found: $state" }
    $entry = (Get-Content -LiteralPath $state -Raw | ConvertFrom-Json).slots | Where-Object { [int]$_.slot -eq $Number }
    if (-not $entry) { throw "slot $Number is not in $state" }
    return $entry.root
}

function Test-UnderRoot($Process, [string]$Root) {
    try { $path = $Process.Path } catch { return $false }
    if (-not $path) { return $false }
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    return [IO.Path]::GetFullPath($path).StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)
}

$script:Root = $null
function Get-GameProcesses {
    $found = @(Get-Process -Name $names -ErrorAction SilentlyContinue)
    if ($All) { return $found }
    @($found | Where-Object { Test-UnderRoot $_ $script:Root })
}

try {
    $targets = @(($Slot -ge 0), [bool]$GameRoot, [bool]$All) | Where-Object { $_ }
    if ($targets.Count -ne 1) {
        Write-Host 'close: ERROR: choose exactly one of -Slot <n>, -GameRoot <folder> or -All' -ForegroundColor Red
        exit 2
    }
    if ($GameRoot) { $script:Root = $GameRoot }
    elseif ($Slot -ge 0) { $script:Root = Resolve-SlotRoot $Slot }
    if ($All) { Write-Host 'close: -All is set: every game of every slot is a target' }
    else { Write-Host ('close: target game folder: {0}' -f $script:Root) }

    $running = Get-GameProcesses
    if ($running.Count -eq 0) {
        Write-Host 'close: the game is not running'
        exit 0
    }
    Write-Host ('close: found {0}' -f (($running | ForEach-Object { "$($_.ProcessName) (PID $($_.Id))" }) -join ', '))
    if ($DryRun) {
        Write-Host 'close: -DryRun is set; nothing was closed'
        exit 0
    }

    foreach ($p in $running) {
        if ($p.MainWindowHandle -ne [IntPtr]::Zero) {
            Write-Host ('close: asking {0} to close' -f $p.ProcessName)
            [void]$p.CloseMainWindow()
        }
    }

    $deadline = (Get-Date).AddSeconds($GraceSeconds)
    while ((Get-Date) -lt $deadline -and (Get-GameProcesses).Count -gt 0) {
        Start-Sleep -Milliseconds 500
    }

    $left = Get-GameProcesses
    if ($left.Count -eq 0) {
        Write-Host 'close: the game closed normally'
        exit 0
    }

    if ($NoForce) {
        Write-Host ('close: still running after {0} s (-NoForce is set)' -f $GraceSeconds)
        exit 1
    }

    Write-Host ('close: still running after {0} s; killing it' -f $GraceSeconds)
    $left | Stop-Process -Force
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline -and (Get-GameProcesses).Count -gt 0) { Start-Sleep -Milliseconds 250 }
    if ((Get-GameProcesses).Count -gt 0) {
        Write-Host 'close: ERROR: the game is still running after the kill'
        exit 2
    }
    Write-Host 'close: the game was killed'
    exit 1
} catch {
    Write-Host "close: ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
