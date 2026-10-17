# Eski kök yapısından src/ yapısına geçiş (arşiv)

**Durum:** Bu değişiklik `main` dalında `6cacd70` commit'i ile tamamlandı. Mevcut projede aşağıdaki eski geçiş komutlarını **yeniden çalıştırma**. Bu belge yalnızca önceki klasör düzeninden yükseltecek eski yerel kopyalar için arşiv niteliğindedir.

Bu işlemler **mevcut Git deposu içinde**, kullanıcı verilerine dokunmadan yapılmalıdır.

## 1. Mevcut projeni yedekle

Uygulamayı kapat. PowerShell ile proje köküne git:

```powershell
cd E:\Projeler\FortniteSplashMaker
git status
```

Özellikle son UI modülleri henüz commit edilmemiş olabilir. Kaynak dosyalarının kopyasını **proje dışındaki** bir klasöre al:

```powershell
$Backup = "E:\Projeler\FortniteSplashMaker-refactor-backup"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Copy-Item .\main.py,.\splash_files.py,.\ui_components.py,.\ui_feedback.py,.\ui_dialogs.py -Destination $Backup -Force
```

Bu komut kodların önceki hâlini korur; `settings.json`, `library/` veya yedeklere müdahale etmez.

## 2. Yeni projeyi mevcut köke çıkart

Hazırlanan **FortniteSplashMaker-src-refactored.zip** arşivini `E:\Projeler\FortniteSplashMaker` içine çıkar ve *aynı adlı kaynak/doküman dosyalarının üzerine yaz*. ZIP içinde `.git/`, kullanıcı `library/` görselleri veya `settings.json` bulunmaz.

**Önemli:** ZIP arşivinin içerdiği `src/` doğrudan proje kökünde olmalı; ikinci bir `FortniteSplashMaker/` katmanı olmamalı.

## 3. Eski kök Python dosyalarını kaldır

Yeni `src/fortnite_splash_maker/` altında ilgili dosyaların oluştuğunu doğruladıktan sonra:

```powershell
Remove-Item .\main.py,.\splash_files.py,.\ui_components.py,.\ui_feedback.py,.\ui_dialogs.py -Force
```

Bu komut **yalnızca beş eski kök Python dosyasını** kaldırır; `library/`, `settings.json`, `assets/` ve `%LOCALAPPDATA%` yedeklerini silmez.

## 4. Test et

```powershell
python -m unittest discover -s tests -p "test*.py" -v
python -m compileall -q src scripts/run.py
python scripts/run.py
```

Uygulama açılınca Oluştur, Kütüphane, Ayarlar ekranlarını ve özellikle mevcut kullanıcı splash'lerini kontrol et.

Windows EXE ve installer'ın yeni yapıda çalıştığını doğrulamak için ayrıca:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```

## 5. Git commit (yalnızca testlerden sonra)

```powershell
git status
git add -A
git status
git commit -m "v1.1.0 kaynak kodlar src paket yapısına taşındı"
git push origin main
```

`git status` üzerinde kişisel dosyalar veya `release/` görünürse **commit etmeden önce durumu incele**. Mevcut v1.0.0 etiketi ve GitHub Release değiştirilmez.
