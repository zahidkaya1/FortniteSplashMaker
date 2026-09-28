# Fortnite Splash Maker — Build

## Geliştirme
```powershell
python main.py
```

## EXE oluşturma
Proje klasöründe:

```powershell
.\build.ps1
```

veya `build.bat` dosyasını çift tıklayın.

Çıktı:

```text
dist/
└─ FortniteSplashMaker/
   ├─ FortniteSplashMaker.exe
   ├─ _internal/
   └─ library/
```

`settings.json` uygulama ilk kez manuel Fortnite yolu kaydettiğinde EXE'nin yanındaki klasörde oluşur.

## Uygulama ikonu
Özel Windows ikonu kullanmak için şu dosyayı ekleyin:

```text
assets/app_icon.ico
```

Dosya varsa `build.ps1` bunu hem EXE ikonu hem de uygulama pencere ikonu olarak kullanır.
