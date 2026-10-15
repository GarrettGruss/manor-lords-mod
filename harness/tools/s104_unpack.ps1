# Convert already extracted assets to JSON (spec 18, issue #104). The AES key comes from the environment only.
# Each asset: a path like ManorLords/Content/CPP_BP/BuildingMasterAssemble/BM_SG_SmallStable (no extension).
param([Parameter(Mandatory = $true)][string[]]$Assets)
$work = "C:\Users\garre\development\manor-lords-mod\modtools\work"
foreach ($asset in $Assets) {
    $windowsPath = $asset.Replace("/", "\")
    if (-not (Test-Path "$work\extracted\$windowsPath.uasset")) {
        uv run python harness\tools\pakmod.py extract $asset | Select-Object -Last 1
    }
    uv run python harness\tools\pakmod.py tojson "$work\extracted\$windowsPath.uasset" | Select-Object -Last 1
}
