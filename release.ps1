$ErrorActionPreference = "Stop"

$Version = "1.0.0"
$AppName = "FortniteSplashMaker"
$DistApp = ".\dist\$AppName"
$ExePath = "$DistApp\$AppName.exe"
$ReleaseRoot = ".\release"
$ReleaseFolder = "$ReleaseRoot\$AppName-v$Version"
$ZipPath = "$ReleaseRoot\$AppName-v$Version-win64.zip"

Write-Host ""
Write-Host "$AppName - v$Version Release Package" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $ExePath)) {
    throw "EXE bulunamadi: $ExePath`nOnce .\build.ps1 ile build al."
}

Write-Host "[1/4] Eski release temizleniyor..."

if (Test-Path $ReleaseFolder) {
    Remove-Item $ReleaseFolder -Recurse -Force
}

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

if (-not (Test-Path $ReleaseRoot)) {
    New-Item -ItemType Directory -Path $ReleaseRoot | Out-Null
}

Write-Host "[2/4] Dağıtım klasörü hazırlanıyor..."

New-Item -ItemType Directory -Path $ReleaseFolder | Out-Null

# PyInstaller onedir çıktısını olduğu gibi kopyala.
Copy-Item "$DistApp\*" $ReleaseFolder -Recurse -Force

# Kullanıcıya özel/veri dosyaları release paketine girmesin.
$SettingsFile = Join-Path $ReleaseFolder "settings.json"
if (Test-Path $SettingsFile) {
    Remove-Item $SettingsFile -Force
}

# Library klasörü boş başlasın.
$LibraryFolder = Join-Path $ReleaseFolder "library"
if (Test-Path $LibraryFolder) {
    Remove-Item $LibraryFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $LibraryFolder | Out-Null

# Basit kullanıcı notu.
$ReadmeText = @"
Fortnite Splash Maker v$Version

Çalıştırmak için:
- FortniteSplashMaker.exe dosyasını açın.

Notlar:
- library klasörü kullanıcı splash görselleri için kullanılır.
- settings.json ilk kullanımda otomatik oluşturulur.
- Fortnite klasörüne yazma izni gerekirse uygulamayı yönetici olarak çalıştırın.
"@

Set-Content `
    -Path (Join-Path $ReleaseFolder "README.txt") `
    -Value $ReadmeText `
    -Encoding UTF8

Write-Host "[3/4] ZIP oluşturuluyor..."

Compress-Archive `
    -Path "$ReleaseFolder\*" `
    -DestinationPath $ZipPath `
    -CompressionLevel Optimal

Write-Host "[4/4] Paket doğrulanıyor..."

if (-not (Test-Path $ZipPath)) {
    throw "Release ZIP oluşturulamadı."
}

$ZipInfo = Get-Item $ZipPath

Write-Host ""
Write-Host "RELEASE HAZIR" -ForegroundColor Green
Write-Host "Klasör: $ReleaseFolder"
Write-Host "ZIP:     $ZipPath"
Write-Host ("Boyut:   {0:N2} MB" -f ($ZipInfo.Length / 1MB))
Write-Host ""
