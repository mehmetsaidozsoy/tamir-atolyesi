import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
import sqlite3
from config import BACKUP_DIR, LOG_FILE, LOG_FORMAT, LOG_LEVEL, MAX_BACKUPS

# Loglama sistemini yapılandır
logging.basicConfig(
    filename=LOG_FILE,
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

def veritabani_yedekle(db_path):
    """Veritabanını yedekler"""
    try:
        # Yedek dosya adını oluştur
        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        yedek_dosya = BACKUP_DIR / f"tamir_atolyesi_{zaman_damgasi}.db"
        
        # Veritabanını yedekle
        shutil.copy2(db_path, yedek_dosya)
        logger.info(f"Veritabanı yedeklendi: {yedek_dosya}")
        
        # Eski yedekleri temizle
        yedekleri_temizle()
        
        return True
    except Exception as e:
        logger.error(f"Veritabanı yedekleme hatası: {str(e)}")
        return False

def yedekleri_temizle():
    """Eski yedekleri temizler"""
    try:
        # Tüm yedek dosyalarını al
        yedekler = list(BACKUP_DIR.glob("tamir_atolyesi_*.db"))
        
        # Maksimum yedek sayısından fazla varsa, en eski yedekleri sil
        if len(yedekler) > MAX_BACKUPS:
            # Dosyaları oluşturulma tarihine göre sırala
            yedekler.sort(key=lambda x: x.stat().st_mtime)
            
            # En eski yedekleri sil
            for yedek in yedekler[:-MAX_BACKUPS]:
                yedek.unlink()
                logger.info(f"Eski yedek silindi: {yedek}")
    except Exception as e:
        logger.error(f"Yedek temizleme hatası: {str(e)}")

def veritabani_baglantisi_kontrol_et(db_path):
    """Veritabanı bağlantısını kontrol eder"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
        return False

def hata_yonetimi(func):
    """Hata yönetimi dekoratörü"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Hata oluştu: {str(e)}")
            raise
    return wrapper

def dosya_yolu_olustur(dizin, dosya_adi):
    """Güvenli dosya yolu oluşturur"""
    try:
        yol = Path(dizin) / dosya_adi
        yol.parent.mkdir(parents=True, exist_ok=True)
        return yol
    except Exception as e:
        logger.error(f"Dosya yolu oluşturma hatası: {str(e)}")
        return None 