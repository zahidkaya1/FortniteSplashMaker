# Build — Fortnite Splash Maker v1.1.0 RC

Proje kökünde Windows PowerShell kullan:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test*.py" -v
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Build scripti proje kökünü kendi dizininden (`$PSScriptRoot`) bulur. PyInstaller giriş dosyası **`scripts/run.py`**; Python paketlerini arama yolu **`src`** (`--paths .\src`), görseller **`assets;assets`** parametresiyle eklenir.

Çıktı: `dist\FortniteSplashMaker\FortniteSplashMaker.exe`.

Derleme tamamlandığında ayrıca `dist\FortniteSplashMaker\build-version.txt` oluşturulur. Bu dosya `1.1.0` değerini içerir ve Setup/portable dağıtım betikleri tarafından kontrol edilir. **Önce yeni EXE, sonra ZIP ve Setup oluşturulmalıdır.** Önceki v1.0.0 EXE'sini yeni sürüm adıyla paketlemek engellenir.

EXE yanında `library/` kullanıcı klasörü ve çalışma sırasında `settings.json` bulunabilir; build ile bunların mevcut kullanıcı içeriği paketlenmez. Kalıcı yedekler `%LOCALAPPDATA%\FortniteSplashMaker\backups` konumunda kalır.

Kurulum, güncelleme ve yayın testleri için [RELEASE.md](RELEASE.md) belgesini kullan.
