"""Splash dosyalarını yedekleyerek ve atomik değiştirerek yönetir."""

import hashlib
import io
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


TARGET_SIZE = (800, 450)


def backup_path_for(target, backup_dir):
    # Windows'ta farklı harf büyüklükleri aynı kuruluma karşılık gelir.
    identity = os.path.normcase(str(Path(target).resolve()))
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return Path(backup_dir) / key / "SplashScreen_previous.png"


def read_png(path):
    data = Path(path).read_bytes()
    validate_png(data)
    return data


def validate_png(data):
    with Image.open(io.BytesIO(data)) as image:
        if image.format != "PNG":
            raise ValueError("Splash dosyası geçerli bir PNG olmalıdır.")
        image.load()


def stage_bytes(destination, data):
    """Tam yazılmış dosyayı hedefle aynı dosya sisteminde hazırlar."""
    destination = Path(destination)
    fd, name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if read_png(temporary) != data:
            raise OSError("Yazılan splash dosyası doğrulanamadı.")
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def ensure_backup(target, backup_dir):
    target = Path(target)
    if target.is_symlink():
        raise ValueError("Splash dosyası bir bağlantı olamaz; gerçek kurulum klasörünü seçin.")
    original = read_png(target)
    backup = backup_path_for(target, backup_dir)
    if backup.exists():
        # Bozuk yedeğin sessizce üzerine yazmak yerine işlemi durdur.
        read_png(backup)
        return backup

    backup.parent.mkdir(parents=True, exist_ok=True)
    temporary = stage_bytes(backup, original)
    try:
        try:
            # Hard link, tamamlanmış yedeği atomik olarak yayımlar ve var olan
            # yedeği ezmez; iki uygulama aynı anda açılsa da ilk yedek korunur.
            os.link(temporary, backup)
        except FileExistsError:
            read_png(backup)
    finally:
        temporary.unlink(missing_ok=True)
    return backup


def atomic_replace_png(target, data):
    target = Path(target)
    validate_png(data)
    if target.is_symlink():
        raise ValueError("Splash dosyası bir bağlantı olamaz.")
    temporary = stage_bytes(target, data)
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def apply_splash(image, target, backup_dir):
    prepared = ImageOps.fit(
        image.convert("RGBA"), TARGET_SIZE,
        method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
    )
    with io.BytesIO() as output:
        prepared.save(output, format="PNG")
        data = output.getvalue()
    ensure_backup(target, backup_dir)
    atomic_replace_png(target, data)


def restore_previous_splash(target, backup_dir):
    backup = backup_path_for(target, backup_dir)
    if not backup.is_file():
        raise FileNotFoundError("Bu Fortnite kurulumu için önceki splash yedeği bulunamadı.")
    # Yeniden boyutlandırma/kodlama yapmadan özgün baytları geri getir.
    atomic_replace_png(target, read_png(backup))
