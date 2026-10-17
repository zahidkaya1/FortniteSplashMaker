# Fortnite Splash Maker

Fortnite'ın Easy Anti-Cheat başlangıç ekranı (`SplashScreen.png`) için özel görselleri hazırlayan, yerel kütüphanede saklayan ve güvenli şekilde uygulayan Windows masaüstü aracı.

**Sürüm durumu:** GitHub'da yayımlanan kararlı sürüm **v1.0.0**. Bu kaynak ağacında **v1.1.0 geliştirmeleri** bulunuyor. Sürüm numarası ve dağıtım paketlerinin adı, v1.1.0 yayına hazırlanırken birlikte güncellenecek.

[Kararlı sürümü indir (v1.0.0)](https://github.com/zahidkaya1/FortniteSplashMaker/releases/tag/v1.0.0)

![Oluştur ekranı (önceki sürüm)](docs/screenshots/create.png)

## Özellikler

- PNG, JPG/JPEG, WEBP ve BMP görsellerini **800×450, PNG, RGBA** biçimine dönüştürür.
- Epic Games Launcher manifestlerinden Fortnite'ı otomatik bulmayı dener; manuel yol seçimini de destekler.
- Splash dosyasını değiştirmeden önce kurulum başına bir yedek alır; atomik dosya değiştirme yapar.
- İlk yedeği ve **paketle gelen sezon görselini** ayrı ayrı geri yükleme/uygulama seçenekleri sunar.
- Splash kütüphanesinde ekleme, silme, arama ve önizleme bulunur.
- Koyu temalı Oluştur, Kütüphane ve Ayarlar ekranlarına sahiptir.
- Rutin bilgilendirmeleri uygulama içinde gösterir.
- Windows EXE, portable ZIP ve Inno Setup kurulum paketi oluşturulabilir.

**Önemli:** Paketle gelen sezon görseli Fortnite'ın o günkü resmî/güncel görseli olmak zorunda değildir. **Yedeklenen splash**, ilk değişiklikte cihazda bulunan dosyadır; ilk dosya daha önce değiştirilmiş olabilir.

## Klasör yapısı

```text
FortniteSplashMaker/
├── src/
│   └── fortnite_splash_maker/
│       ├── __init__.py
│       ├── __main__.py
│       ├── main.py
│       ├── splash_files.py
│       └── ui/
│           ├── __init__.py
│           ├── components.py
│           ├── dialogs.py
│           └── feedback.py
├── assets/
│   ├── app_icon.ico
│   ├── app_icon.png
│   └── current_season_splash.png
├── docs/
│   ├── screenshots/
│   ├── BUILD.md
│   ├── INSTALLER.md
│   ├── MIGRATION.md
│   └── RELEASE.md
├── installer/
│   └── installer.iss
├── library/
│   └── .gitkeep
├── scripts/
│   ├── run.py
│   ├── run.bat
│   ├── build.ps1
│   ├── build.bat
│   ├── build-installer.ps1
│   ├── build-installer.bat
│   ├── release.ps1
│   └── release.bat
├── tests/
│   ├── test_v11_regressions.py
│   └── test_project_layout.py
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Geliştirme ortamında çalıştırma

**Gerekenler:** Windows 10/11, Python 3.10+ (geliştirme ve paketleme için Python 3.12 önerilir).

Proje kökünde:

```powershell
python -m pip install -r requirements.txt
python scripts/run.py
```

Alternatif olarak paketi düzenlenebilir biçimde kurup modül olarak başlatabilirsin:

```powershell
python -m pip install -e .
python -m fortnite_splash_maker
```

> Eski `python main.py` komutu yeni yapıda kullanılmaz; uygulama kaynakları `src/` altına taşındı. **Doğrudan çalıştırma için `python scripts/run.py` kullan.**

## Testler

```powershell
python -m unittest discover -s tests -p "test*.py" -v
python -m compileall -q src scripts/run.py
```

Bu testler GUI davranışlarının belirli kısımlarını ve dosya yönetimini kontrol eder. Gerçek Windows penceresi, EXE ve Setup ayrıca manuel test edilmelidir.

## Windows build ve dağıtım

Normal EXE build:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

Çıktı: `dist\FortniteSplashMaker\FortniteSplashMaker.exe`

Portable ZIP:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```

Inno Setup kurulum dosyası (Inno Setup 6 kurulu olmalıdır):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```

**Dikkat:** Kaynak geliştirme aşamasında sürüm alanları hâlâ **1.0.0** değerindedir. v1.1.0 sürüm numarası, release/installer dosya adları ve açıklamaları yayın aşamasında birlikte yükseltilmelidir. Buradan oluşturulan yeni paketleri eski **v1.0.0 GitHub Release** dosyalarının üzerine yükleme.

Ayrıntılar: [Build](docs/BUILD.md), [Installer](docs/INSTALLER.md), [Release](docs/RELEASE.md).

## Kaynak klasör yapısına geçiş

Mevcut Git deposunu ve kullanıcı verilerini koruyarak geçmek için [MIGRATION.md](docs/MIGRATION.md) belgesini izle. ZIP dosyasını proje köküne çıkarınca eski kök Python dosyaları otomatik silinmez; bunlar doğrulama sonrası kaldırılmalıdır.

## Veri konumları

- `library/` — uygulamanın yanındaki kullanıcı görselleri.
- `settings.json` — kurulum yolu dahil kullanıcı ayarları, uygulamanın yanındaki dosya.
- `%LOCALAPPDATA%\FortniteSplashMaker\backups` — ilk splash yedeği; uygulamadan/EXE'den bağımsız.
- `assets/` — **kaynak proje** için paketle gelen kaynaklar (build sırasında EXE'ye dahil edilir).

`library/` görselleri, `settings.json`, `build/`, `dist/`, `release/` ve Python önbellekleri Git'e gönderilmez. Kaynak ZIP kullanıcı kütüphanesini ve ayarlarını içermez; var olanlara dokunmaz.

## Yetkiler ve yasal not

Fortnite dosyasına yazma izni yoksa izinlerin kontrol edilmesi veya uygulamanın yönetici olarak açılması gerekebilir. İmzalanmamış Windows uygulamaları bazı bilgisayarlarda SmartScreen uyarısı gösterebilir.

Bu, Epic Games tarafından geliştirilmemiş veya desteklenmemiş bağımsız bir topluluk aracıdır. Fortnite ve ilgili markalar Epic Games'e aittir.
