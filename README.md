# Fortnite Splash Maker

Fortnite Easy Anti-Cheat başlangıç ekranını kolayca değiştirmek, özel splash görselleri hazırlamak ve yerel bir kütüphanede saklamak için geliştirilmiş Windows masaüstü uygulaması.

![Fortnite Splash Maker](docs/screenshots/create.png)

## Özellikler

- Fortnite Easy Anti-Cheat splash görselini değiştirme
- PNG, JPG, JPEG, WEBP ve BMP desteği
- Görselleri otomatik olarak 800×450 PNG RGBA formatına hazırlama
- Fortnite kurulumunu otomatik algılama
- Manuel Fortnite klasörü seçme ve yolu hatırlama
- Yerel splash kütüphanesi
- Kütüphaneye görsel ekleme, silme ve tekrar uygulama
- Aktif sezon splash görselini geri yükleme
- Aktif splash durumunu algılama
- Windows için paketlenmiş EXE sürümü
- Windows Setup desteği
- Özel uygulama ikonu

## Kütüphane

Hazırladığınız splash görsellerini uygulamanın yerel kütüphanesinde saklayabilirsiniz.

Kütüphane üzerinden:

- Yeni görsel ekleyebilirsiniz
- Görselleri önizleyebilirsiniz
- Daha önce kaydettiğiniz bir splash'i tekrar Fortnite'a uygulayabilirsiniz
- Kayıtlı görselleri silebilirsiniz
- Aktif sezon splash görseline hızlıca dönebilirsiniz

![Kütüphane](docs/screenshots/library.png)

## Ayarlar

Ayarlar sayfasından Fortnite kurulum yolunu görüntüleyebilir veya değiştirebilirsiniz.

Uygulama mümkün olduğunda Fortnite kurulumunu Epic Games Launcher verilerinden otomatik olarak algılar.

![Ayarlar](docs/screenshots/settings.png)

## İndirme

En güncel sürümü GitHub Releases sayfasından indirebilirsiniz.

### Önerilen

`FortniteSplashMaker-v1.0.0-Setup.exe`

Normal Windows kurulumu yapar.

Kurulum sonrasında uygulamayı Başlat menüsünden veya oluşturmayı seçtiyseniz masaüstü kısayolundan çalıştırabilirsiniz.

### Portable

`FortniteSplashMaker-v1.0.0-win64.zip`

ZIP dosyasını bir klasöre çıkarın ve `FortniteSplashMaker.exe` dosyasını çalıştırın.

## Kullanım

1. Uygulamayı açın.
2. Fortnite kurulumu otomatik olarak algılanır.
3. Algılanamazsa Fortnite klasörünü manuel olarak seçin.
4. `Görsel Seç` butonuyla kullanmak istediğiniz resmi seçin.
5. Uygulama görseli otomatik olarak 800×450 RGBA PNG formatına hazırlar.
6. `Fortnite'a Uygula` butonuna basın.
7. İsterseniz hazırladığınız görseli kütüphaneye ekleyin.
8. Varsayılan splash'e dönmek için `Aktif Sezon Splash'ini Geri Yükle` seçeneğini kullanın.

## Görsel Formatı

Fortnite splash görselleri uygulama tarafından otomatik olarak şu formata dönüştürülür:

- Boyut: `800×450`
- Format: `PNG`
- Renk modu: `RGBA`
- Yeniden boyutlandırma: merkez odaklı otomatik kırpma

Bu sayede farklı boyut ve oranlardaki görseller doğrudan kullanılabilir.

## Proje Yapısı

```text
FortniteSplashMaker/
├─ assets/
│  ├─ app_icon.ico
│  ├─ app_icon.png
│  └─ current_season_splash.png
│
├─ docs/
│  └─ screenshots/
│     ├─ create.png
│     ├─ library.png
│     └─ settings.png
│
├─ library/
│
├─ main.py
├─ requirements.txt
│
├─ build.ps1
├─ build.bat
├─ BUILD.md
│
├─ release.ps1
├─ release.bat
├─ RELEASE.md
│
├─ installer.iss
├─ build-installer.ps1
├─ build-installer.bat
├─ INSTALLER.md
│
├─ .gitignore
└─ README.md
```

`build/`, `dist/`, `release/`, `settings.json` ve kullanıcı kütüphanesi Git tarafından takip edilmez.

## Gereksinimler

Kaynak koddan çalıştırmak için:

- Windows
- Python 3.12 veya üzeri
- CustomTkinter
- Pillow
- PyInstaller

Bağımlılıkları yüklemek için:

```powershell
pip install -r requirements.txt
```

## Kaynak Koddan Çalıştırma

```powershell
python main.py
```

## Windows EXE Oluşturma

Proje klasöründe:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

veya:

```text
build.bat
```

Build tamamlandığında uygulama şu klasörde oluşturulur:

```text
dist\FortniteSplashMaker\
```

Ana çalıştırılabilir dosya:

```text
dist\FortniteSplashMaker\FortniteSplashMaker.exe
```

Uygulama PyInstaller `onedir` yapısıyla paketlenir.

## Windows Installer Oluşturma

Installer oluşturmak için önce normal uygulama build'inin hazır olması gerekir.

### 1. EXE build oluşturun

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

### 2. Inno Setup 6

Installer derlemek için Inno Setup 6 gereklidir.

### 3. Installer oluşturun

```powershell
powershell -ExecutionPolicy Bypass -File .\build-installer.ps1
```

veya:

```text
build-installer.bat
```

Başarılı build sonrasında:

```text
release\FortniteSplashMaker-v1.0.0-Setup.exe
```

dosyası oluşturulur.

Installer varsayılan olarak uygulamayı kullanıcı profili altındaki Programs klasörüne kurar.

## Release Paketi Oluşturma

Portable ZIP paketi hazırlamak için:

```powershell
powershell -ExecutionPolicy Bypass -File .\release.ps1
```

veya:

```text
release.bat
```

Çıktı:

```text
release\FortniteSplashMaker-v1.0.0-win64.zip
```

Release paketi kullanıcıya ait `settings.json` dosyasını içermez ve boş bir kütüphane ile hazırlanır.

## Ayarlar ve Kullanıcı Verileri

Uygulama çalışırken `settings.json` dosyası otomatik olarak oluşturulabilir.

Kullanıcının eklediği splash görselleri `library\` klasöründe tutulur.

Bu dosyalar kişisel kullanıcı verisi olduğu için Git deposunda takip edilmez.

## Aktif Sezon Splash

Uygulamanın kullandığı bilinen aktif sezon splash görseli:

```text
assets\current_season_splash.png
```

dosyasında bulunur.

`Aktif Sezon Splash'ini Geri Yükle` seçeneği bu görseli Fortnite'ın Easy Anti-Cheat splash dosyasına uygular.

## Yetki Sorunları

Fortnite kurulum klasörüne yazma izni yoksa uygulama hata verebilir.

Bu durumda uygulamayı yönetici olarak çalıştırmayı deneyebilirsiniz.

## Windows SmartScreen

Uygulama ticari bir kod imzalama sertifikasıyla imzalanmadığı için Windows bazı sistemlerde SmartScreen uyarısı gösterebilir.

Bu durum özellikle yeni veya az indirilmiş bağımsız uygulamalarda görülebilir.

## Sürüm

Güncel sürüm: `v1.0.0`

## Lisans ve Yasal Uyarı

Bu proje bağımsız bir topluluk aracıdır.

Epic Games tarafından geliştirilmemiş, desteklenmemiş veya resmî olarak onaylanmamıştır.

Fortnite ve ilgili marka, logo ve isimler Epic Games'in mülkiyetindedir.

Bu proje yalnızca kullanıcıların kendi yerel Fortnite kurulumlarındaki splash görselini yönetmesini kolaylaştırmak amacıyla geliştirilmiştir.
