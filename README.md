# Fortnite Splash Maker

Fortnite'ın Easy Anti-Cheat başlangıç splash görselini hızlıca hazırlamak, saklamak ve değiştirmek için geliştirilmiş Windows masaüstü uygulaması.

![Fortnite Splash Maker - Oluştur](docs/screenshots/create.png)

## Özellikler

- PNG, JPG, JPEG, WEBP ve BMP görsellerini destekler.
- Seçilen görseli otomatik olarak **800×450 PNG RGBA** biçimine hazırlar.
- Görseli 16:9 oranında merkezden kırpar.
- Fortnite kurulumunu Epic Games Launcher manifestlerinden otomatik algılamaya çalışır.
- Fortnite klasörü manuel olarak seçilebilir.
- Manuel seçilen Fortnite yolu sonraki açılışlar için `settings.json` içinde saklanır.
- Hazırlanan splash tek tıkla Fortnite'a uygulanabilir.
- Yerel splash kütüphanesi bulunur.
- Kütüphaneye görsel ekleme, silme ve yeniden uygulama desteklenir.
- Bu sezon için tanımlanmış **Aktif Sezon Splash** tek tıkla geri yüklenebilir.
- Mevcut Fortnite splash'i kontrol edilerek:
  - **Aktif Sezon Splash**
  - **Özel Splash**

  durumu gösterilir.
- Windows için `.exe` olarak paketlenebilir.
- Uygulama ve EXE için özel ikon desteği bulunur.

## Kütüphane

Kullandığın splash görsellerini uygulama içinde saklayabilir ve daha sonra tekrar uygulayabilirsin.

![Fortnite Splash Maker - Kütüphane](docs/screenshots/library.png)

Kütüphaneye eklenen görseller varsayılan olarak:

```text
Splash 01
Splash 02
Splash 03
...
```

şeklinde isimlendirilir. İstenirse ekleme sırasında özel bir isim de verilebilir.

## Ayarlar

Ayarlar ekranından Fortnite kurulum yolu değiştirilebilir veya kayıtlı yol sıfırlanabilir.

![Fortnite Splash Maker - Ayarlar](docs/screenshots/settings.png)

Manuel olarak seçilen Fortnite yolu proje / uygulama klasöründeki:

```text
settings.json
```

dosyasında saklanır.

## Kullanım

1. Uygulamayı aç.
2. **Görsel Seç** butonuyla kullanmak istediğin görseli seç.
3. Görsel otomatik olarak Fortnite için uygun biçime hazırlanır.
4. **Fortnite'a Uygula** butonuna bas.
5. İstersen görseli **Kütüphaneye Ekle** ile sakla.
6. Varsayılan güncel splash'e dönmek için **Aktif Sezon Splash'ini Geri Yükle** seçeneğini kullan.

## Proje Yapısı

```text
FortniteSplashMaker/
├─ assets/
│  ├─ app_icon.ico
│  ├─ app_icon.png
│  └─ current_season_splash.png
├─ docs/
│  └─ screenshots/
│     ├─ create.png
│     ├─ library.png
│     └─ settings.png
├─ library/
├─ .gitignore
├─ build.bat
├─ BUILD.md
├─ build.ps1
├─ main.py
├─ README.md
└─ requirements.txt
```

`library/` kullanıcı tarafından eklenen splash görselleri için kullanılır.

## Gereksinimler

Kaynak koddan çalıştırmak için:

- Windows
- Python 3.12+
- CustomTkinter
- Pillow

Bağımlılıkları yüklemek için:

```powershell
python -m pip install -r requirements.txt
```

Uygulamayı çalıştırmak için:

```powershell
python main.py
```

## EXE Oluşturma

Projede PyInstaller tabanlı build betiği bulunur.

PowerShell üzerinden:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

veya:

```text
build.bat
```

dosyasını çalıştırabilirsin.

Başarılı build sonrasında çıktı:

```text
dist/
└─ FortniteSplashMaker/
   ├─ FortniteSplashMaker.exe
   ├─ _internal/
   └─ library/
```

konumunda oluşturulur.

## Sürüm

**v1.0.0**

## Notlar

- Fortnite güncellemeleri Easy Anti-Cheat klasör yapısını veya splash dosyasını değiştirebilir.
- Fortnite klasörüne yazma izni olmayan sistemlerde uygulamayı yönetici olarak çalıştırmak gerekebilir.
- `current_season_splash.png`, uygulamanın geri yükleme için kullandığı mevcut sezon splash görselidir ve sezon değiştiğinde güncellenebilir.

## Yasal Not

Bu proje bağımsız bir topluluk aracıdır; Epic Games tarafından geliştirilmemiş veya desteklenmemiştir.

**Fortnite** ve ilgili markalar Epic Games, Inc.'e aittir.
