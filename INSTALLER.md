# Fortnite Splash Maker v1.0.0 Installer

Kurulum dosyası **Inno Setup 6** ile oluşturulur.

## 1. Uygulamayı build et

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

## 2. Inno Setup 6 kur

Resmî site:

https://jrsoftware.org/isdl.php

## 3. Installer oluştur

```powershell
powershell -ExecutionPolicy Bypass -File .\build-installer.ps1
```

veya `build-installer.bat` dosyasını çift tıkla.

Çıktı:

```text
release/
└─ FortniteSplashMaker-v1.0.0-Setup.exe
```

Kurulum kullanıcı bazlıdır ve varsayılan olarak:

```text
%LOCALAPPDATA%\Programs\FortniteSplashMaker
```

konumuna kurulur. Böylece uygulamanın `settings.json` ve `library` klasörünü yönetici izni gerektirmeden yazabilmesi amaçlanır.
