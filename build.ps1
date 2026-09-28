$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Fortnite Splash Maker - v1.0.0 Build" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\main.py")) {
    throw "main.py bulunamadi. build.ps1 dosyasini proje klasorunden calistir."
}

if (-not (Test-Path ".\assets\current_season_splash.png")) {
    throw "assets\current_season_splash.png bulunamadi."
}

Write-Host "[1/4] Bagimliliklar kontrol ediliyor..."
python -m pip install -r requirements.txt

Write-Host "[2/4] Eski build temizleniyor..."
if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}
if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

Write-Host "[3/4] EXE olusturuluyor..."

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

Write-Host "[4/4] Yazilabilir library klasoru hazirlaniyor..."
$distApp = ".\dist\FortniteSplashMaker"

if (-not (Test-Path "$distApp\library")) {
    New-Item -ItemType Directory -Path "$distApp\library" | Out-Null
}

Write-Host ""
Write-Host "BUILD TAMAMLANDI" -ForegroundColor Green
Write-Host "Cikti: $distApp\FortniteSplashMaker.exe"
Write-Host ""
