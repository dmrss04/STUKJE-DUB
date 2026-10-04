# Builds DUB and produces the installer: installer\Output\DUB-Setup.exe
# Needs: Python with pyinstaller, pillow, pycaw, comtypes, aalink  +  Inno Setup 6
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$app = Split-Path $here -Parent
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($env:DUB_PYTHON) { $py = $env:DUB_PYTHON }
$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
          "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $py) { throw "Python not found (set DUB_PYTHON)." }
if (-not $iscc) { throw "Inno Setup 6 not found (winget install JRSoftware.InnoSetup)." }

$build = Join-Path $here "build"
Remove-Item (Join-Path $build "dist"), (Join-Path $build "work"), (Join-Path $build "spec") -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $build | Out-Null

Write-Host "== images"
& $py (Join-Path $here "make_images.py"); if ($LASTEXITCODE) { throw "images" }

$ico = Join-Path $app "dub.ico"
$dist = Join-Path $build "dist"; $work = Join-Path $build "work"; $specs = Join-Path $build "spec"
Push-Location $app
try {
    Write-Host "== DUB.exe"
    & $py -m PyInstaller --noconfirm --onedir --windowed --name DUB --icon $ico `
        --hidden-import pycaw.pycaw --hidden-import comtypes.client --hidden-import comtypes.client.dynamic `
        --collect-all aalink --distpath $dist --workpath $work --specpath $specs (Join-Path $app "dub.py")
    if ($LASTEXITCODE) { throw "pyinstaller DUB" }
    Write-Host "== dub-statusline.exe"
    & $py -m PyInstaller --noconfirm --onedir --console --name dub-statusline --icon $ico `
        --distpath $dist --workpath $work --specpath $specs (Join-Path $app "dub_statusline.py")
    if ($LASTEXITCODE) { throw "pyinstaller statusline" }
} finally { Pop-Location }

Write-Host "== installer"
& $iscc (Join-Path $here "DUB.iss"); if ($LASTEXITCODE) { throw "inno setup" }
Write-Host "`nDone: $here\Output\DUB-Setup.exe"
