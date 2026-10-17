# Portable Release

Önce Windows EXE'sini oluştur:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Sonra portable paketi oluştur:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```

Mevcut betikteki sürüm değeri değiştirilene dek çıktı:

```text
release\FortniteSplashMaker-v1.0.0-win64.zip
```

Script `dist/` içeriğini kopyalar, dağıtım paketinden `settings.json` ve kullanıcı `library/` içeriğini çıkarır, temiz bir `library/` klasörü oluşturur.

**v1.1.0 yayınlanmadan önce:** `APP_VERSION`, `pyproject.toml` sürümü, `scripts/release.ps1`, `scripts/build-installer.ps1`, `installer/installer.iss` ve README sürüm referansları birlikte güncellenecek; ardından EXE, ZIP ve Setup yeniden oluşturulup test edilecek.
