# Windows Installer

**Gereken:** Inno Setup 6. Script, `%LOCALAPPDATA%\Programs\Inno Setup 6` ve standart Program Files konumlarını kontrol eder.

Önce EXE derle:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Ardından installer oluştur:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```

`installer/installer.iss`, derlenen `dist\FortniteSplashMaker\` klasörünü paketler. Uygulamanın `src/` altına taşınması installer'daki `Source:` hedefini değiştirmez.

Çıktı: `release\FortniteSplashMaker-v1.0.0-Setup.exe` (v1.1.0 yayınlanmadan önceki dosya adı).

**Yayın notu:** `installer.iss` içindeki sürüm ve OutputBaseFilename, ayrıca build/release scriptleri ve uygulama sürümü v1.1.0 yayın hazırlığında beraber güncellenmelidir. Önce yeni kurulum test edilmeli, sonra GitHub Release'e yüklenmelidir.
