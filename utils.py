import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
import sqlite3
from config import BACKUP_DIR, LOG_FILE, LOG_FORMAT, LOG_LEVEL, MAX_BACKUPS
import hashlib
import re
import json
from typing import Union, Dict, Any
import math

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

def format_currency(amount):
    """Para birimini formatlar"""
    try:
        return f"{float(amount):,.2f} ₺"
    except (ValueError, TypeError):
        return "0.00 ₺"

def validate_phone(phone):
    """Telefon numarasını doğrular"""
    import re
    phone = re.sub(r'\D', '', phone)  # Sadece rakamları al
    if len(phone) != 10:
        return False
    return bool(re.match(r'^[5][0-9]{9}$', phone))

def validate_email(email):
    """E-posta adresini doğrular"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_tc(tc):
    """TC Kimlik numarasını doğrular"""
    if not tc.isdigit() or len(tc) != 11:
        return False
    
    digits = [int(d) for d in str(tc)]
    
    # 1. 10 basamağın toplamının birler basamağı 11. basamağa eşit olmalı
    if sum(digits[:10]) % 10 != digits[10]:
        return False
    
    # Diğer algoritma kontrolleri
    if digits[0] == 0:
        return False
    
    if ((7 * sum(digits[0:9:2])) - sum(digits[1:9:2])) % 10 != digits[9]:
        return False
    
    return True

def parola_hash(parola: str) -> str:
    """Parolayı SHA-256 ile hashler"""
    return hashlib.sha256(parola.encode()).hexdigest()

def tc_no_dogrula(tc_no: str) -> bool:
    """TC Kimlik numarasının geçerliliğini kontrol eder"""
    if not tc_no.isdigit() or len(tc_no) != 11 or tc_no[0] == '0':
        return False
        
    digits = [int(d) for d in tc_no]
    
    # 1, 3, 5, 7, 9. hanelerin toplamının 7 katından, 2, 4, 6, 8. hanelerin toplamı çıkartıldığında,
    # elde edilen sonucun 10'a bölümünden kalan, yani Mod10'u bize 10. haneyi verir.
    if ((sum(digits[0:9:2]) * 7) - sum(digits[1:8:2])) % 10 != digits[9]:
        return False
    
    # 1'den 10'uncu haneye kadar olan rakamların toplamından elde edilen sonucun
    # 10'a bölümünden kalan, bize 11'inci haneyi verir.
    if sum(digits[:10]) % 10 != digits[10]:
        return False
        
    return True

def plaka_dogrula(plaka: str) -> bool:
    """Araç plakasının geçerliliğini kontrol eder"""
    # Türkiye plaka formatı: 34 ABC 123 veya 34 AB 123
    pattern = r'^\d{2}\s?[A-Z]{2,3}\s?\d{2,4}$'
    return bool(re.match(pattern, plaka.upper()))

def para_formatla(tutar: float) -> str:
    """Para tutarını formatlı şekilde döndürür"""
    return f"{tutar:,.2f} ₺"

def tarih_formatla(tarih: datetime) -> str:
    """Tarihi formatlı şekilde döndürür"""
    return tarih.strftime("%d.%m.%Y %H:%M")

def json_kaydet(dosya: Path, veri: Dict[str, Any]) -> bool:
    """Veriyi JSON formatında kaydeder"""
    try:
        with open(dosya, 'w', encoding='utf-8') as f:
            json.dump(veri, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"JSON kaydetme hatası: {str(e)}")
        return False

def json_oku(dosya: Path) -> Union[Dict[str, Any], None]:
    """JSON dosyasından veri okur"""
    try:
        with open(dosya, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"JSON okuma hatası: {str(e)}")
        return None

def telefon_formatla(telefon: str) -> str:
    """Telefon numarasını formatlı şekilde döndürür"""
    # Sadece rakamları al
    rakamlar = ''.join(filter(str.isdigit, telefon))
    
    if len(rakamlar) == 10:  # 5XX XXX XXXX
        return f"{rakamlar[:3]} {rakamlar[3:6]} {rakamlar[6:]}"
    elif len(rakamlar) == 11:  # 0 5XX XXX XXXX
        return f"{rakamlar[1:4]} {rakamlar[4:7]} {rakamlar[7:]}"
    else:
        return telefon  # Geçersiz format, olduğu gibi döndür

def email_dogrula(email: str) -> bool:
    """E-posta adresinin geçerliliğini kontrol eder"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def dosya_boyutu_formatla(boyut: int) -> str:
    """
    Dosya boyutunu okunabilir formata dönüştürür.
    
    Args:
        boyut (int): Bayt cinsinden dosya boyutu
        
    Returns:
        str: Formatlanmış dosya boyutu (örn: "1.5 MB")
    """
    if boyut == 0:
        return "0 B"
    
    birimler = ['B', 'KB', 'MB', 'GB', 'TB']
    i = int(math.floor(math.log(boyut, 1024)))
    p = math.pow(1024, i)
    s = round(boyut / p, 2)
    
    return f"{s} {birimler[i]}"

def onarim_durumu_renk(durum: str) -> str:
    """Onarım durumuna göre renk kodu döndürür"""
    renkler = {
        'Beklemede': '#FFA500',  # Turuncu
        'Devam Ediyor': '#FFD700',  # Altın
        'Tamamlandı': '#32CD32',  # Lime Yeşili
        'İptal Edildi': '#FF0000',  # Kırmızı
        'Parça Bekliyor': '#4169E1',  # Royal Mavi
    }
    return renkler.get(durum, '#000000')  # Varsayılan siyah

def izin_seviyesi_adi(seviye: int) -> str:
    """İzin seviyesinin adını döndürür"""
    seviyeler = {
        0: 'Ziyaretçi',
        1: 'Teknisyen',
        2: 'Yönetici',
        3: 'Admin'
    }
    return seviyeler.get(seviye, 'Bilinmiyor')

def gecerli_email_mi(email: str) -> bool:
    """
    E-posta adresinin geçerli olup olmadığını kontrol eder.
    
    Args:
        email (str): Kontrol edilecek e-posta adresi
        
    Returns:
        bool: E-posta adresi geçerli ise True, değilse False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def gecerli_telefon_mu(telefon: str) -> bool:
    """
    Telefon numarasının geçerli olup olmadığını kontrol eder.
    
    Args:
        telefon (str): Kontrol edilecek telefon numarası
        
    Returns:
        bool: Telefon numarası geçerli ise True, değilse False
    """
    # Sadece rakamları al
    rakamlar = ''.join(filter(str.isdigit, telefon))
    
    # Türkiye telefon numarası formatı: 10 veya 11 rakam
    return len(rakamlar) in (10, 11)

def gecerli_plaka_mi(plaka: str) -> bool:
    """
    Araç plakasının geçerli olup olmadığını kontrol eder.
    
    Args:
        plaka (str): Kontrol edilecek plaka
        
    Returns:
        bool: Plaka geçerli ise True, değilse False
    """
    # Türkiye plaka formatı: 34 ABC 123 veya 34ABC123
    pattern = r'^[0-9]{2}[A-Z]{1,3}[0-9]{2,4}$'
    
    # Boşlukları kaldır ve büyük harfe çevir
    plaka = ''.join(plaka.split()).upper()
    
    return bool(re.match(pattern, plaka))

def tarih_formatla(tarih: Union[str, datetime], format: str = "%d.%m.%Y") -> str:
    """
    Tarihi belirtilen formata dönüştürür.
    
    Args:
        tarih (Union[str, datetime]): Formatlanacak tarih
        format (str, optional): Çıktı formatı. Defaults to "%d.%m.%Y".
        
    Returns:
        str: Formatlanmış tarih
    """
    try:
        if isinstance(tarih, str):
            # Tarih string ise datetime'a çevir
            tarih = datetime.strptime(tarih, format)
        return tarih.strftime(format)
    except Exception as e:
        logger.error(f"Tarih formatlama hatası: {e}")
        return ""

def para_formatla(tutar: float) -> str:
    """
    Para tutarını Türk Lirası formatında formatlar.
    
    Args:
        tutar (float): Formatlanacak tutar
        
    Returns:
        str: Formatlanmış tutar (örn: "1.234,56 ₺")
    """
    try:
        return f"{tutar:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception as e:
        logger.error(f"Para formatla hatası: {e}")
        return "0,00 ₺"

def klasor_olustur(klasor_yolu: Union[str, Path]) -> bool:
    """
    Belirtilen klasörü oluşturur.
    
    Args:
        klasor_yolu (Union[str, Path]): Oluşturulacak klasörün yolu
        
    Returns:
        bool: Klasör oluşturma başarılı ise True, değilse False
    """
    try:
        if isinstance(klasor_yolu, str):
            klasor_yolu = Path(klasor_yolu)
        
        klasor_yolu.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Klasör oluşturma hatası: {e}")
        return False

def dosya_sil(dosya_yolu: Union[str, Path]) -> bool:
    """
    Belirtilen dosyayı siler.
    
    Args:
        dosya_yolu (Union[str, Path]): Silinecek dosyanın yolu
        
    Returns:
        bool: Dosya silme başarılı ise True, değilse False
    """
    try:
        if isinstance(dosya_yolu, str):
            dosya_yolu = Path(dosya_yolu)
        
        if dosya_yolu.exists():
            dosya_yolu.unlink()
            return True
        return False
    except Exception as e:
        logger.error(f"Dosya silme hatası: {e}")
        return False

def parola_guclu_mu(parola: str) -> tuple[bool, str]:
    """
    Parolanın güçlü olup olmadığını kontrol eder.
    
    Args:
        parola (str): Kontrol edilecek parola
        
    Returns:
        tuple[bool, str]: (Parola güçlü ise True, değilse False, Hata mesajı)
    """
    if len(parola) < 8:
        return False, "Parola en az 8 karakter olmalıdır."
    
    if not re.search(r"[A-Z]", parola):
        return False, "Parola en az bir büyük harf içermelidir."
    
    if not re.search(r"[a-z]", parola):
        return False, "Parola en az bir küçük harf içermelidir."
    
    if not re.search(r"[0-9]", parola):
        return False, "Parola en az bir rakam içermelidir."
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", parola):
        return False, "Parola en az bir özel karakter içermelidir."
    
    return True, "Parola güçlü."

def tc_kimlik_gecerli_mi(tc_kimlik: str) -> bool:
    """
    TC Kimlik numarasının geçerli olup olmadığını kontrol eder.
    
    Args:
        tc_kimlik (str): Kontrol edilecek TC Kimlik numarası
        
    Returns:
        bool: TC Kimlik numarası geçerli ise True, değilse False
    """
    try:
        # Sadece rakamları al
        tc_kimlik = ''.join(filter(str.isdigit, tc_kimlik))
        
        if not tc_kimlik.isdigit() or len(tc_kimlik) != 11 or tc_kimlik[0] == '0':
            return False
        
        digits = [int(d) for d in str(tc_kimlik)]
        
        # 1, 3, 5, 7, 9. hanelerin toplamının 7 katından, 2, 4, 6, 8. hanelerin toplamı çıkartıldığında,
        # elde edilen sonucun 10'a bölümünden kalan, yani Mod10'u bize 10. haneyi verir.
        if ((sum(digits[0:9:2]) * 7) - sum(digits[1:8:2])) % 10 != digits[9]:
            return False
        
        # İlk 10 hanenin toplamının 10'a bölümünden kalan, bize 11. haneyi verir.
        if sum(digits[:10]) % 10 != digits[10]:
            return False
        
        return True
    except Exception:
        return False

def vergi_no_gecerli_mi(vergi_no: str) -> bool:
    """
    Vergi numarasının geçerli olup olmadığını kontrol eder.
    
    Args:
        vergi_no (str): Kontrol edilecek vergi numarası
        
    Returns:
        bool: Vergi numarası geçerli ise True, değilse False
    """
    try:
        # Sadece rakamları al
        vergi_no = ''.join(filter(str.isdigit, vergi_no))
        
        if not vergi_no.isdigit() or len(vergi_no) != 10:
            return False
        
        digits = [int(d) for d in str(vergi_no)]
        
        # Son hane kontrol hanesidir
        control_digit = digits[-1]
        
        # Her bir rakam için (10 - sıra numarası) ile çarpılır ve mod 10 alınır
        total = 0
        for i in range(9):
            digit = digits[i]
            multiplier = (10 - i)
            product = (digit * multiplier) % 10
            if product != 0:
                total += (9 - product)
        
        # Hesaplanan toplam 10'a bölünür ve kalan kontrol hanesi ile karşılaştırılır
        calculated_control = (10 - (total % 10)) % 10
        
        return calculated_control == control_digit
    except Exception:
        return False 