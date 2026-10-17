"""Kaynak koddan calistirma: python scripts/run.py

Kurulum gerekmeden src paketini bulur; PyInstaller'in giris dosyasidir.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from fortnite_splash_maker.__main__ import main


if __name__ == "__main__":
    main()
