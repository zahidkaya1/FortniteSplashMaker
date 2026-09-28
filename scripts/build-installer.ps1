$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$AppName = "FortniteSplashMaker"
$Version = "1.0.0"
$DistExe = ".\dist\$AppName\$AppName.exe"
$IssFile = ".\installer\installer.iss"

Write-Host ""
Write-Host "Fortnite Splash Maker - v$Version Installer Build" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $DistExe)) {
    throw "EXE bulunamadi: $DistExe`nOnce .\scripts\build.ps1 ile uygulamayi build edin."
}

if (-not (Test-Path $IssFile)) {
    throw "installer\installer.iss bulunamadi."
}

$PossibleIsccPaths = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)

$Iscc = $null

foreach ($Candidate in $PossibleIsccPaths) {
    if ($Candidate -and (Test-Path $Candidate)) {
        $Iscc = $Candidate
        break
    }
}

if (-not $Iscc) {
    Write-Host "Inno Setup 6 bulunamadi." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Once Inno Setup 6 kurun, sonra bu scripti tekrar calistirin."
    Write-Host "Resmi site: https://jrsoftware.org/isdl.php"
    Write-Host ""
    throw "Inno Setup 6 gerekli."
}

Write-Host "Inno Setup bulundu:"
Write-Host $Iscc
Write-Host ""

if (-not (Test-Path ".\release")) {
    New-Item -ItemType Directory -Path ".\release" | Out-Null
}

$runningApps = Get-Process -Name $AppName -ErrorAction SilentlyContinue
if ($runningApps) {
    Write-Host "Calisan FortniteSplashMaker.exe kapatiliyor..." -ForegroundColor Yellow
    $runningApps | Stop-Process -Force
    Start-Sleep -Milliseconds 800
}

Write-Host "Kurulum dosyasi olusturuluyor..."

& $Iscc $IssFile

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup build basarisiz oldu."
}

$SetupPath = ".\release\FortniteSplashMaker-v1.0.0-Setup.exe"

if (-not (Test-Path $SetupPath)) {
    throw "Setup EXE olusturulamadi: $SetupPath"
}

$SetupInfo = Get-Item $SetupPath

Write-Host ""
Write-Host "INSTALLER HAZIR" -ForegroundColor Green
Write-Host "Cikti: $SetupPath"
Write-Host ("Boyut: {0:N2} MB" -f ($SetupInfo.Length / 1MB))
Write-Host ""
