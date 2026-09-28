# v1.0.0 Release Paketi

Önce EXE build'i alın:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Ardından temiz kullanıcı dağıtım ZIP'ini oluşturun:

```powershell
powershell -ExecutionPolicy Bypass -File .\release.ps1
```

veya `release.bat` dosyasını çift tıklayın.

Oluşacak dosya:

```text
release/
└─ FortniteSplashMaker-v1.0.0-win64.zip
```

ZIP içinde kullanıcıya özel `settings.json` bulunmaz ve `library/` klasörü boş başlar.
