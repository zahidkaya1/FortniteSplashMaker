# Release

Önce normal build'i oluşturun:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Ardından portable release paketini hazırlayın:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```

Çıktı:

```text
release\FortniteSplashMaker-v1.0.0-win64.zip
```
