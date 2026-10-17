# Windows Installer — v1.1.0 RC

**Gereken:** Inno Setup 6. Betik, `%LOCALAPPDATA%\Programs\Inno Setup 6` ve standart Program Files konumlarını kontrol eder.

Önce yeni sürümün EXE dosyasını derle:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Ardından Installer oluştur:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```

`installer/installer.iss`, `dist\FortniteSplashMaker\` içeriğini paketler. `build-installer.ps1`, `build-version.txt` değerinin `1.1.0` olduğunu kontrol eder; eşleşmezse hata verir.

**Beklenen çıktı:** `release\FortniteSplashMaker-v1.1.0-Setup.exe`.

Kaynak kodun `src/` altına taşınması installer'daki `Source:` konumunu değiştirmez. Uygulama sürümü ve Windows Installer sürüm bilgileri `1.1.0` olarak güncellenmiştir.

**Veri notu:** Mevcut installer konfigürasyonunda kaldırma sırasında `{app}\settings.json` dosyası temizlenir. Test için önce ayarları ve kullanıcı `library/` içeriğini yedekle; kurulu eski sürümü kaldırarak değil, öncelikle kontrollü sürüm yükseltmesiyle test et. Yedeklenmiş splash dosyaları `%LOCALAPPDATA%\FortniteSplashMaker\backups` içinde tutulur.

Kurulmuş uygulamanın çalışması doğrulanmadan Git etiketi veya GitHub Release oluşturma. Ayrıntılar: [RELEASE.md](RELEASE.md).
