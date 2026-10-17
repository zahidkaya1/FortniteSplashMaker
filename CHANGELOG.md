# Değişiklik Günlüğü

Bu belge yayımlanan sürümleri ve yayıma hazırlanan değişiklikleri kaydeder.

## [1.1.0] — Release Candidate (henüz yayımlanmadı)

### Eklendi

- Ortak koyu tema kart, düğme ve durum rozeti bileşenleri.
- Uygulama içinde başarı, bilgi, uyarı ve hata bildirimleri.
- Kütüphaneye isim verme ve işlem onayı için ortak, koyu temalı pencereler.
- Kütüphane arama ve seçim vurgusu; aktif splash durumunu Ayarlar ekranından kontrol etme.
- `src/fortnite_splash_maker/` paket düzeni, `pyproject.toml`, paket giriş noktası ve `scripts/run.py`.
- Otomatik regresyon ve proje yapısı testleri.

### Değiştirildi

- Oluştur, Kütüphane ve Ayarlar ekranlarının düzeni ve geri bildirim yerleşimi iyileştirildi.
- Görseller ve hata bildirimleri, önceki arayüz bileşenlerinin üzerine taşmadan gösteriliyor.
- PyInstaller giriş noktası `scripts/run.py` olarak güncellendi; kaynak, test ve belge yolları yeni paket yapısıyla uyumlu hâle getirildi.
- Uygulama ve Installer sürüm alanları `1.1.0` değerine çıkarıldı.
- EXE derlemesi bir sürüm kaydı üretiyor; Setup ve portable ZIP betikleri sürüm uyuşmazlığında duruyor.

### Düzeltildi

- Geçersiz/bozuk görsel seçimi sonrasında eski önizlemenin ekranda kalması.
- Bozuk yedek dosyasının değişiklikten önce denetlenmemesiyle ilişkili riskler.
- Kütüphane kartlarının yerleşim ve görsel referansı sorunları.
- Sekmeler arasında geçişte eski bildirimlerin kalması ve bildirimlerin başka bileşenlerin üzerine binmesi.
- Aktif splash'ın paketlenmiş sezon görseliyle karşılaştırılması ve belirsiz durumların gösterilmesi.

### Sürüm notları

- `v1.1.0` henüz Git etiketi veya GitHub Release olarak yayımlanmadı. Windows EXE, portable ZIP ve Setup'ın son manuel kontrolleri tamamlanınca yayımlanacak.
- Kullanıcı kütüphanesi, kurulum ayarları ve `%LOCALAPPDATA%\FortniteSplashMaker\backups` yedek konumu bu sürümde değiştirilmedi.
- Paketle gelen sezon görseli, Fortnite'ın güncel resmî görseli olarak garanti edilmez.

## [1.0.0] — İlk kararlı sürüm

- Görselleri 800×450 PNG biçimine dönüştürme ve önizleme.
- Fortnite kurulumunu algılama, elle klasör seçme ve splash uygulama.
- Mevcut splash için yedek alma, önceki splash'ı geri yükleme ve paketli sezon görselini uygulama.
- Yerel görsel kütüphanesi ve uygulama ayarları.
- Windows EXE, portable ZIP ve Inno Setup dağıtımları.

[1.0.0]: https://github.com/zahidkaya1/FortniteSplashMaker/releases/tag/v1.0.0
