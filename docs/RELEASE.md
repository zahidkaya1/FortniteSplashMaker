# v1.1.0 Release Candidate ve yayın kontrol listesi

**Durum:** v1.1.0 kaynak sürümü hazırlanmıştır; henüz etiketlenip yayımlanmamıştır. GitHub'daki son yayımlanmış kararlı sürüm **v1.0.0** olarak kalır.

## 1. Sürüm denetimi

Şu alanların tümü `1.1.0` olmalıdır:

- `src/fortnite_splash_maker/main.py` → `APP_VERSION`
- `pyproject.toml` → `[project].version`
- `scripts/build.ps1`, `scripts/release.ps1`, `scripts/build-installer.ps1` → `$Version`
- `installer/installer.iss` → `MyAppVersion`, Windows sürüm alanları ve Setup dosya adı
- `CHANGELOG.md` → henüz yayımlanmamış v1.1.0 kaydı

Otomatik sürüm tutarlılığı testleri `tests/test_release_metadata.py` içindedir.

## 2. Kaynaktan test

Windows PowerShell, proje kökünde:

```powershell
python -m unittest discover -s tests -p "test*.py" -v
python -m compileall -q src scripts/run.py
python scripts/run.py
```

Oluştur, Kütüphane, Ayarlar ekranlarını; geçersiz görsel hatasını; isimlendirme/onay pencerelerini kontrol et. Önceki kullanıcı görsellerinin ve ayarların korunduğundan emin ol.

## 3. Sıfırdan paketleme

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```

**Beklenen çıktılar:**

```text
dist\FortniteSplashMaker\FortniteSplashMaker.exe
release\FortniteSplashMaker-v1.1.0-win64.zip
release\FortniteSplashMaker-v1.1.0-Setup.exe
```

`build.ps1` EXE yanına `build-version.txt` dosyası oluşturur. Portable ZIP ve Setup betikleri bu kayıttaki sürüm `1.1.0` değilse **paketlemeyi durdurur**. Böylece eski v1.0.0 derlemesi yanlışlıkla v1.1.0 adıyla yayımlanmaz. EXE'yi değiştirdikten sonra paketleri yeniden oluştur.

## 4. Windows manuel doğrulama

- `dist` içindeki EXE, `release` ZIP'inden çıkarılmış portable EXE ve Setup üzerinden kurulu EXE ayrı ayrı açılmalı.
- Üç ekran; PNG/JPG/WEBP giriş ve PDF hata bildirimi; kütüphaneye ekleme, arama ve silme; isimlendirme, `Esc`, `Enter`, onay/iptal kontrol edilmeli.
- Ayarlarda sürüm `1.1.0` görünmeli; Fortnite yolu, kullanıcı `library/` görselleri ve yedek durumu doğru kalmalı.
- Gerçek Fortnite splash'ını değiştirme testi istenirse önce mevcut dosya ve kullanıcı verileri yedeklenmeli; özellikle geri yükleme işlemi kontrollü denenmeli.
- Önceki kurulu sürümün üzerine kurulum ve kaldırma işlemleri, **ayrı bir test ortamında veya kullanıcı verileri yedeklenerek** denenmeli. Mevcut installer tanımında kaldırma sırasında `{app}\settings.json` dosyası silinir.
- Kurulumun Windows izinleri ve güvenlik uyarıları gibi platform davranışları manuel doğrulanmalı.

## 5. Yayımlamadan önce

1. Tüm testler ve manuel kontroller tamamlanmalı.
2. `CHANGELOG.md` içindeki `Release Candidate` ifadesi gerçek yayın tarihiyle güncellenmeli.
3. Kod ve belge değişiklikleri commit edilip `main` dalına gönderilmeli; çalışma ağacı temiz olmalı.
4. **Yalnızca bu noktada** `v1.1.0` Git etiketi oluşturulmalı ve GitHub Release açılmalı.
5. `FortniteSplashMaker-v1.1.0-win64.zip` ve `FortniteSplashMaker-v1.1.0-Setup.exe` dosyaları yayıma eklenmeli.
6. Mevcut v1.0.0 GitHub Release ve etiketi değiştirilmemeli.

**Not:** Bu kaynak paketi hazır EXE/Setup içermiyor. Windows derlemesi ve kurulum doğrulaması kullanıcı bilgisayarında yapılmalıdır.
