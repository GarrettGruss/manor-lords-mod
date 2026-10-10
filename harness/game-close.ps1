<#
.SYNOPSIS
  Closes Manor Lords. Asks the game to close first. Kills it only if it does not close in time.
.DESCRIPTION
  1. Sends a close request to the game window (like the user clicking the close button).
  2. Waits up to -GraceSeconds for the game to exit.
  3. If it is still running, kills it (unless -NoForce is set).
  A normal close lets UE4SS write its log to disk. A kill can lose the end of UE4SS.log.
  The script does not touch save files.
.PARAMETER GraceSeconds
  How long to wait after the close request. Default 20.
.PARAMETER NoForce
  Never kill the game. Exit with code 1 if it is still running after the wait.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness\game-close.ps1
.NOTES
  Exit codes: 0 = closed normally or not running, 1 = killed or still running (see message), 2 = error.
#>
[CmdletBinding()]
param(
    [int]$GraceSeconds = 20,
    [switch]$NoForce
)
$ErrorActionPreference = 'Stop'

# The game process and the launcher stub that starts it.
$names = @('ManorLords-Win64-Shipping', 'ManorLords')

function Get-GameProcesses {
    @(Get-Process -Name $names -ErrorAction SilentlyContinue)
}

try {
    $running = Get-GameProcesses
    if ($running.Count -eq 0) {
        Write-Host 'close: the game is not running'
        exit 0
    }
    Write-Host ('close: found {0}' -f (($running | ForEach-Object { "$($_.ProcessName) (PID $($_.Id))" }) -join ', '))

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
