# Shared functions for install.ps1 and uninstall.ps1 (spec 11, design 10). Dot-source this file.
#
# The game reads and writes its settings in the REAL user folder, not in a private LOCALAPPDATA.
# So the harness backs up the user's files once, writes its own values, and restores the backup at uninstall.

$script:UserFiles = @('Config\Windows\GameUserSettings.ini', 'Config\Windows\UserSettings.ini', 'SaveGames\rtsSettings.sav')

# Values the harness wants: low quality, a small window, 30 fps. Keys that are not listed stay as the user has them.
$script:HarnessIniValues = @{
    'Config\Windows\UserSettings.ini' = [ordered]@{
        'Settings' = [ordered]@{
            'ML.tutorials' = 'false'; 'ML.aaMode' = 'none'; 'r.ngx.dlss.enable' = '0'; 'r.VSync' = '0'
            'Foliage.LODDistanceScale' = '0.3'; 'ML.grassDistance' = '0.2'; 'ML.grassDensity' = '0.2'
            'r.ViewDistanceScale' = '0.4'; 'r.VolumetricFog' = '0'; 'ML.volumetricClouds' = 'false'; 'r.volumetriccloud' = '0'
            'r.LightShaftQuality' = '0'; 'r.BloomQuality' = '0'; 'r.MaterialQualityLevel' = '0'; 'r.Streaming.PoolSize' = '400'
            'sg.ResolutionQuality' = '50'; 'sg.ViewDistanceQuality' = '0'; 'sg.AntiAliasingQuality' = '0'; 'sg.ShadowQuality' = '0'
            'sg.GlobalIlluminationQuality' = '0'; 'sg.ReflectionQuality' = '0'; 'sg.PostProcessQuality' = '0'; 'sg.TextureQuality' = '0'
            'sg.EffectsQuality' = '0'; 'sg.FoliageQuality' = '0'; 'sg.ShadingQuality' = '0'; 'sg.LandscapeQuality' = '0'
            't.MaxFps' = '30'; 'r.setres' = '1280x720w'
        }
    }
    'Config\Windows\GameUserSettings.ini' = [ordered]@{
        'ScalabilityGroups' = [ordered]@{
            'sg.ResolutionQuality' = '50'; 'sg.ViewDistanceQuality' = '0'; 'sg.AntiAliasingQuality' = '0'; 'sg.ShadowQuality' = '0'
            'sg.GlobalIlluminationQuality' = '0'; 'sg.ReflectionQuality' = '0'; 'sg.PostProcessQuality' = '0'; 'sg.TextureQuality' = '0'
            'sg.EffectsQuality' = '0'; 'sg.FoliageQuality' = '0'; 'sg.ShadingQuality' = '0'; 'sg.LandscapeQuality' = '0'
        }
        '/Script/Engine.GameUserSettings' = [ordered]@{
            'bUseVSync' = 'False'; 'ResolutionSizeX' = '1280'; 'ResolutionSizeY' = '720'
            'LastUserConfirmedResolutionSizeX' = '1280'; 'LastUserConfirmedResolutionSizeY' = '720'
            'FullscreenMode' = '2'; 'LastConfirmedFullscreenMode' = '2'; 'PreferredFullscreenMode' = '2'; 'FrameRateLimit' = '30.000000'
        }
    }
}

# Read-only game data that every slot shares through a junction. Paths are relative to the game root.
$script:SlotJunctions = @('Engine', 'ManorLords\Plugins', 'ManorLords\Content\Movies', 'ManorLords\Content\Slate')

function Get-InstallDir([string]$SlotsDir) { Join-Path $SlotsDir '.install' }
function Get-SettingsStatePath([string]$SlotsDir) { Join-Path (Get-InstallDir $SlotsDir) 'settings.json' }
function Get-SlotsStatePath([string]$SlotsDir) { Join-Path (Get-InstallDir $SlotsDir) 'slots.json' }

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Assert-GameNotRunning {
    if (Get-Process -Name 'ManorLords-Win64-Shipping', 'ManorLords' -ErrorAction SilentlyContinue) {
        throw 'The game is running. It writes its settings when it exits, so stop it first.'
    }
}

function Assert-Inside([string]$Root, [string]$Path) {
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    if (-not [IO.Path]::GetFullPath($Path).StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to touch a path outside ${Root}: $Path"
    }
}

# The state names the game folder it was made for. An uninstall for another folder (a test with a temp game) leaves it alone.
function Test-SameGameDir($State, [string]$GameDir) {
    if (-not $State.game_dir) { return $true }  # a state from before this field: it can only be the real install
    return [IO.Path]::GetFullPath($State.game_dir).TrimEnd('') -ieq [IO.Path]::GetFullPath($GameDir).TrimEnd('')
}

function Write-TextAtomic([string]$Path, [string]$Text) {
    $tmp = "$Path.tmp"
    [IO.File]::WriteAllText($tmp, $Text, (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

function Copy-FileAtomic([string]$Source, [string]$Target) {
    $tmp = "$Target.tmp"
    Copy-Item -LiteralPath $Source -Destination $tmp -Force
    Move-Item -LiteralPath $tmp -Destination $Target -Force
}

# ---- ini merge ----

# Set keys in ini text. A key that exists in its section is replaced in place; a missing key goes to the end of its section.
function Set-IniValues([string]$Text, $Sections) {
    $eol = if ($Text.Contains("`r`n") -or $Text.Length -eq 0) { "`r`n" } else { "`n" }
    $lines = New-Object System.Collections.Generic.List[string]
    if ($Text.Length -gt 0) { $lines.AddRange([string[]]($Text.TrimEnd("`r", "`n") -split "\r?\n")) }
    foreach ($section in $Sections.Keys) {
        $values = $Sections[$section]
        $start = $lines.IndexOf("[$section]")
        if ($start -lt 0) {
            if ($lines.Count -gt 0) { $lines.Add('') }
            $lines.Add("[$section]")
            $start = $lines.Count - 1
        }
        $end = $start + 1
        while ($end -lt $lines.Count -and -not $lines[$end].StartsWith('[')) { $end++ }
        foreach ($key in $values.Keys) {
            $line = "$key=$($values[$key])"
            $found = $false
            for ($i = $start + 1; $i -lt $end; $i++) {
                if ($lines[$i].StartsWith("$key=", [StringComparison]::OrdinalIgnoreCase)) { $lines[$i] = $line; $found = $true; break }
            }
            if ($found) { continue }
            # Insert before the blank lines that end the section, so the layout stays the same.
            $at = $end
            while ($at -gt $start + 1 -and $lines[$at - 1].Trim() -eq '') { $at-- }
            $lines.Insert($at, $line)
            $end++
        }
    }
    return ($lines -join $eol) + $eol
}

# ---- user settings: backup, harness values, restore ----

function Backup-UserFiles([string]$UserDir, [string]$SlotsDir, [string]$GameDir) {
    $statePath = Get-SettingsStatePath $SlotsDir
    if (Test-Path -LiteralPath $statePath) {
        Write-Host 'settings   backup exists from an earlier install; it is kept, not replaced'
        return
    }
    $backupDir = Join-Path (Get-InstallDir $SlotsDir) 'backup'
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $entries = @()
    foreach ($relative in $script:UserFiles) {
        $source = Join-Path $UserDir $relative
        $entry = [ordered]@{ path = $relative; existed = (Test-Path -LiteralPath $source); sha256 = $null }
        if ($entry.existed) {
            $target = Join-Path $backupDir ($relative -replace '\\', '__')
            Copy-Item -LiteralPath $source -Destination $target
            $entry.sha256 = Get-Sha256 $source
            if ((Get-Sha256 $target) -ne $entry.sha256) { throw "Backup copy differs from its source: $relative" }
        }
        $entries += $entry
        Write-Host ("settings   backed up  {0} ({1})" -f $relative, $(if ($entry.existed) { 'exists' } else { 'not present' }))
    }
    # The state is written before the first change, so an uninstall can always find the backup.
    Write-TextAtomic $statePath (ConvertTo-Json @{ user_dir = $UserDir; game_dir = $GameDir; files = $entries } -Depth 4)
}

function Set-HarnessUserSettings([string]$UserDir) {
    foreach ($relative in $script:HarnessIniValues.Keys) {
        $path = Join-Path $UserDir $relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
        $text = if (Test-Path -LiteralPath $path) { [IO.File]::ReadAllText($path) } else { '' }
        Write-TextAtomic $path (Set-IniValues $text $script:HarnessIniValues[$relative])
        Write-Host "settings   harness values written to $relative"
    }
}

function Restore-UserFiles([string]$SlotsDir, [string]$GameDir) {
    $statePath = Get-SettingsStatePath $SlotsDir
    if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'settings   no install backup found: nothing to restore'; return 0 }
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if (-not (Test-SameGameDir $state $GameDir)) {
        Write-Host "settings   the install backup belongs to $($state.game_dir), not to this GameDir: left alone"
        return 0
    }
    $backupDir = Join-Path (Get-InstallDir $SlotsDir) 'backup'
    $restored = 0
    foreach ($entry in $state.files) {
        $target = Join-Path $state.user_dir $entry.path
        if ($entry.existed) {
            $backup = Join-Path $backupDir ($entry.path -replace '\\', '__')
            if ((Get-Sha256 $backup) -ne $entry.sha256) { throw "Backup file changed since install, not restored: $($entry.path)" }
            Copy-FileAtomic $backup $target
            if ((Get-Sha256 $target) -ne $entry.sha256) { throw "Restore check failed (hash differs): $($entry.path)" }
            Write-Host "settings   restored   $($entry.path)"
        } elseif (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Force  # the file did not exist before the install
            Write-Host "settings   removed    $($entry.path) (it did not exist before the install)"
        }
        $restored++
    }
    # Only a full, verified restore removes the backup.
    Remove-Item -LiteralPath $backupDir -Recurse -Force
    Remove-Item -LiteralPath $statePath -Force
    return $restored
}

# ---- slots ----

function Get-SlotRoot([string]$SlotsDir, [int]$Slot) { Join-Path (Join-Path $SlotsDir $Slot) 'Manor Lords' }

function Invoke-Robocopy([string]$Source, [string]$Target) {
    & robocopy $Source $Target /E /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed with code $LASTEXITCODE`: $Source" }
}

function New-Slot([string]$GameDir, [string]$SlotsDir, [int]$Slot) {
    $root = Get-SlotRoot $SlotsDir $Slot
    if (Test-Path -LiteralPath $root) { Write-Host "slot $Slot     exists, kept: $root"; return $null }
    $gamePaks = Join-Path $GameDir 'ManorLords\Content\Paks'
    if ((Split-Path -Qualifier $gamePaks) -ne (Split-Path -Qualifier ([IO.Path]::GetFullPath($SlotsDir)))) {
        throw 'Slots must be on the same drive as the game: the paks are hard links.'
    }
    $junctions = @()
    foreach ($relative in $script:SlotJunctions) {
        $link = Join-Path $root $relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $link) | Out-Null
        New-Item -ItemType Junction -Path $link -Target (Join-Path $GameDir $relative) | Out-Null
        $junctions += $relative
    }
    Invoke-Robocopy (Join-Path $GameDir 'ManorLords\Binaries\Win64') (Join-Path $root 'ManorLords\Binaries\Win64')
    $paks = Join-Path $root 'ManorLords\Content\Paks'
    New-Item -ItemType Directory -Force -Path $paks | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath $gamePaks -Force) {
        # ~mods stays per slot and starts empty, so pak A/B tests do not mix between slots.
        if ($item.PSIsContainer) {
            if ($item.Name -ne '~mods') { Invoke-Robocopy $item.FullName (Join-Path $paks $item.Name) }
            continue
        }
        New-Item -ItemType HardLink -Path (Join-Path $paks $item.Name) -Target $item.FullName | Out-Null
    }
    Write-Host "slot $Slot     built: $root"
    return [ordered]@{ slot = $Slot; root = $root; junctions = $junctions }
}

function Remove-Slot([string]$SlotsDir, $Entry) {
    $root = $Entry.root
    # The delete is of the parent slots\<n>, so the parent must also be inside, never slots\ itself.
    Assert-Inside $SlotsDir (Split-Path -Parent $root)
    if (-not (Test-Path -LiteralPath $root)) { Write-Host "slot $($Entry.slot)     not present"; return }
    # Junctions go first, as links. A recursive delete through a junction would delete game files.
    foreach ($relative in $Entry.junctions) {
        $link = Join-Path $root $relative
        if (-not (Test-Path -LiteralPath $link)) { continue }
        if ((Get-Item -LiteralPath $link -Force).LinkType -ne 'Junction') { throw "Expected a junction, found a normal folder: $link" }
        [IO.Directory]::Delete($link, $false)
    }
    $links = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint -ErrorAction Stop)
    if ($links.Count -gt 0) { throw "Slot still has links, not deleted: $($links[0].FullName)" }
    Remove-Item -LiteralPath (Split-Path -Parent $root) -Recurse -Force
    Write-Host "slot $($Entry.slot)     removed"
}

function Read-SlotsState([string]$SlotsDir, [string]$GameDir) {
    $path = Get-SlotsStatePath $SlotsDir
    if (-not (Test-Path -LiteralPath $path)) { return @() }
    $state = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    if (-not (Test-SameGameDir $state $GameDir)) {
        Write-Host "slots      the slots belong to $($state.game_dir), not to this GameDir: left alone"
        return @()
    }
    return @($state.slots)
}

function Write-SlotsState([string]$SlotsDir, $Entries, [string]$GameDir) {
    New-Item -ItemType Directory -Force -Path (Get-InstallDir $SlotsDir) | Out-Null
    Write-TextAtomic (Get-SlotsStatePath $SlotsDir) (ConvertTo-Json @{ game_dir = $GameDir; slots = @($Entries) } -Depth 4)
}
