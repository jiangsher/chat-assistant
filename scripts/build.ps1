$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }
$AppName = "ChatAssistant"
$DistDir = Join-Path $ProjectRoot "dist"
$AppDistDir = Join-Path $DistDir $AppName
$ZipPath = Join-Path $DistDir "$AppName-windows.zip"

Push-Location $ProjectRoot
try {
    Remove-Item -LiteralPath (Join-Path $ProjectRoot "build") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $AppDistDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $ZipPath -Force -ErrorAction SilentlyContinue

    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name $AppName `
        --paths src `
        src\recognize\__main__.py

    Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination $AppDistDir -Force
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination $AppDistDir -Force

    Compress-Archive -Path (Join-Path $AppDistDir "*") -DestinationPath $ZipPath -Force
    Write-Host "Built $ZipPath"
}
finally {
    Pop-Location
}
