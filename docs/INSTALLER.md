# Installer

Windows installer, Inno Setup 6 ile oluşturulur.

Önce uygulamayı build edin:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Ardından installer oluşturun:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```

Çıktı:

```text
release\FortniteSplashMaker-v1.0.0-Setup.exe
```

Installer varsayılan olarak:

```text
%LOCALAPPDATA%\Programs\FortniteSplashMaker
```

konumuna kurulur.
