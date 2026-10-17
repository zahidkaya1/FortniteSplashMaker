# Build — Fortnite Splash Maker

Proje kökünde Windows PowerShell kullan:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test*.py" -v
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Build scripti proje kökünü kendi dizininden (`$PSScriptRoot`) bulur.
PyInstaller giriş dosyası **`scripts/run.py`**; paketleri bulma yolu **`src`** (`--paths .\src`), görseller **`assets;assets`** veri parametresiyle eklenir.

Çıktı: `dist\FortniteSplashMaker\FortniteSplashMaker.exe`.

EXE yanında `library/` kullanıcı klasörü ve çalışma sırasında `settings.json` bulunabilir; build ile bunların kullanıcı sürümü paketlenmez. Kalıcı yedekler `%LOCALAPPDATA%\FortniteSplashMaker\backups` konumunda kalır.

**Not:** v1.1.0 geliştirme süresince gösterilen uygulama sürümü ve yayın betikleri hâlâ v1.0.0 olarak kalabilir; yeni sürüm yayınından önce birlikte güncellenecek.
