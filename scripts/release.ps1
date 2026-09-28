$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

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
    throw "EXE bulunamadi: $ExePath`nOnce .\scripts\build.ps1 ile build alin."
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

Write-Host "[2/4] Dagitim klasoru hazirlaniyor..."

New-Item -ItemType Directory -Path $ReleaseFolder | Out-Null
Copy-Item "$DistApp\*" $ReleaseFolder -Recurse -Force

$SettingsFile = Join-Path $ReleaseFolder "settings.json"
if (Test-Path $SettingsFile) {
    Remove-Item $SettingsFile -Force
}

$LibraryFolder = Join-Path $ReleaseFolder "library"
if (Test-Path $LibraryFolder) {
    Remove-Item $LibraryFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $LibraryFolder | Out-Null

$ReadmeText = @"
Fortnite Splash Maker v$Version

Calistirmak icin:
- FortniteSplashMaker.exe dosyasini acin.

Notlar:
- library klasoru kullanici splash gorselleri icin kullanilir.
- settings.json ilk kullanimda otomatik olusturulur.
- Fortnite klasorune yazma izni gerekirse uygulamayi yonetici olarak calistirin.
"@

Set-Content `
    -Path (Join-Path $ReleaseFolder "README.txt") `
    -Value $ReadmeText `
    -Encoding UTF8

Write-Host "[3/4] ZIP olusturuluyor..."

Compress-Archive `
    -Path "$ReleaseFolder\*" `
    -DestinationPath $ZipPath `
    -CompressionLevel Optimal

Write-Host "[4/4] Paket dogrulaniyor..."

if (-not (Test-Path $ZipPath)) {
    throw "Release ZIP olusturulamadi."
}

$ZipInfo = Get-Item $ZipPath

Write-Host ""
Write-Host "RELEASE HAZIR" -ForegroundColor Green
Write-Host "Klasor: $ReleaseFolder"
Write-Host "ZIP:     $ZipPath"
Write-Host ("Boyut:   {0:N2} MB" -f ($ZipInfo.Length / 1MB))
Write-Host ""
