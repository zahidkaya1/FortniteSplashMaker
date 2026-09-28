$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host ""
Write-Host "Fortnite Splash Maker - v1.0.0 Build" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\main.py")) {
    throw "main.py bulunamadi. Proje yapisini kontrol edin."
}

if (-not (Test-Path ".\assets\current_season_splash.png")) {
    throw "assets\current_season_splash.png bulunamadi."
}

function Remove-DirectorySafe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    $maxAttempts = 5

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -eq $maxAttempts) {
                throw
            }

            Write-Host "Klasor su anda kullanimda. Tekrar deneniyor... ($attempt/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Milliseconds 800
        }
    }
}

Write-Host "[1/5] Bagimliliklar kontrol ediliyor..."

python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    throw "Bagimliliklar yuklenemedi."
}

Write-Host "[2/5] Calisan eski uygulama kontrol ediliyor..."

$runningApps = Get-Process -Name "FortniteSplashMaker" -ErrorAction SilentlyContinue

if ($runningApps) {
    Write-Host "Calisan FortniteSplashMaker.exe kapatiliyor..." -ForegroundColor Yellow
    $runningApps | Stop-Process -Force
    Start-Sleep -Seconds 1
}

Write-Host "[3/5] Eski build temizleniyor..."

try {
    Remove-DirectorySafe ".\build"
    Remove-DirectorySafe ".\dist"
}
catch {
    Write-Host ""
    Write-Host "Eski build klasoru temizlenemedi." -ForegroundColor Red
    Write-Host "FortniteSplashMaker.exe, Dosya Gezgini onizlemesi veya baska bir program dist klasorundeki dosyalari kullaniyor olabilir." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tum Fortnite Splash Maker pencerelerini kapatip tekrar deneyin." -ForegroundColor Yellow
    throw
}

Write-Host "[4/5] EXE olusturuluyor..."

$pyInstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--onedir",
    "--name", "FortniteSplashMaker",
    "--add-data", "assets;assets"
)

if (Test-Path ".\assets\app_icon.ico") {
    Write-Host "Ozel uygulama ikonu bulundu."
    $pyInstallerArgs += @(
        "--icon", ".\assets\app_icon.ico"
    )
}
else {
    Write-Host "assets\app_icon.ico bulunamadi; EXE simdilik varsayilan ikonla paketlenecek." -ForegroundColor Yellow
}

$pyInstallerArgs += "main.py"

python -m PyInstaller @pyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build basarisiz oldu."
}

Write-Host "[5/5] Yazilabilir library klasoru hazirlaniyor..."

$distApp = ".\dist\FortniteSplashMaker"

if (-not (Test-Path "$distApp\library")) {
    New-Item -ItemType Directory -Path "$distApp\library" | Out-Null
}

Write-Host ""
Write-Host "BUILD TAMAMLANDI" -ForegroundColor Green
Write-Host "Cikti: $distApp\FortniteSplashMaker.exe"
Write-Host ""
