import sqlite3
import logging
from pathlib import Path
import os
from config import DB_PATH
from utils import veritabani_yedekle, veritabani_baglantisi_kontrol_et, hata_yonetimi, logger
from models import Musteri, Tamir, MaliyetTahmini
from datetime import datetime
import hashlib
import shutil
import io
import tempfile

logger = logging.getLogger(__name__)

class VeritabaniYonetici:
    def __init__(self):
        """Veritabanı bağlantısını başlatır"""
        try:
            self.conn = sqlite3.connect("tamir_atolyesi.db")
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            self.tablolari_olustur()
            logger.info("Veritabanı bağlantısı başarılı")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
            raise Exception(f"Veritabanı bağlantı hatası: {str(e)}")

    def __del__(self):
        """Veritabanı bağlantısını kapatır"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                logger.info("Veritabanı bağlantısı kapatıldı")
        except Exception as e:
            logger.error(f"Veritabanı kapatma hatası: {str(e)}")
            pass

    def tablolari_olustur(self):
        """Gerekli tabloları oluşturur"""
        try:
            cursor = self.conn.cursor()
            
            # Kullanıcılar tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kullanicilar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT UNIQUE NOT NULL,
                    sifre_hash TEXT NOT NULL,
                    yetki_seviyesi INTEGER DEFAULT 0,
                    kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Müşteriler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS musteriler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tc_no TEXT UNIQUE,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    telefon TEXT,
                    eposta TEXT,
                    adres TEXT,
                    kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tamirler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tamirler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    musteri_id INTEGER NOT NULL,
                    cihaz_turu TEXT NOT NULL,
                    marka TEXT,
                    model TEXT,
                    seri_no TEXT,
                    sikayet TEXT,
                    ariza TEXT,
                    islemler TEXT,
                    parcalar TEXT,
                    iscilik_ucreti REAL DEFAULT 0,
                    parca_ucreti REAL DEFAULT 0,
                    toplam_ucret REAL DEFAULT 0,
                    durum TEXT DEFAULT 'Beklemede',
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
                    guncelleme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (musteri_id) REFERENCES musteriler(id) ON DELETE CASCADE
                )
            """)
            
            # Yedekler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS yedekler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
                    dosya_adi TEXT,
                    boyut INTEGER,
                    aciklama TEXT,
                    dosya BLOB
                )
            """)
            
            # Ayarlar tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ayarlar (
                    anahtar TEXT PRIMARY KEY,
                    deger TEXT
                )
            """)
            
            self.conn.commit()
            
            # Varsayılan admin kullanıcısını ekle
            cursor.execute("""
                INSERT OR IGNORE INTO kullanicilar (kullanici_adi, sifre_hash, yetki_seviyesi)
                VALUES (?, ?, ?)
            """, ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 1))
            self.conn.commit()
            
            logger.info("Tablolar başarıyla oluşturuldu")
            
        except Exception as e:
            logger.error(f"Tablo oluşturma hatası: {str(e)}")
            raise Exception(f"Tablo oluşturma hatası: {str(e)}")

    def varsayilan_admin_ekle(self):
        """Varsayılan admin kullanıcısını ekler"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO kullanicilar (kullanici_adi, sifre_hash, yetki_seviyesi)
                VALUES (?, ?, ?)
            ''', ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 1))
            self.conn.commit()
            logger.info("Varsayılan admin kullanıcısı kontrol edildi")
        except sqlite3.Error as e:
            logger.error(f"Varsayılan admin ekleme hatası: {str(e)}")
            
    def ayar_ekle(self, anahtar, deger):
        """Yeni ayar ekler"""
        try:
            self.cursor.execute('''
                INSERT INTO ayarlar (anahtar, deger)
                VALUES (?, ?)
            ''', (anahtar, deger))
            self.conn.commit()
            logger.info(f"Yeni ayar eklendi: {anahtar}")
            return True
        except sqlite3.IntegrityError:
            # Ayar zaten varsa güncelle
            return self.ayar_guncelle(anahtar, deger)
        except sqlite3.Error as e:
            logger.error(f"Ayar ekleme hatası: {str(e)}")
            return False

    def ayar_guncelle(self, anahtar, deger):
        """Ayar değerini günceller"""
        try:
            self.cursor.execute('''
                UPDATE ayarlar 
                SET deger=?
                WHERE anahtar=?
            ''', (deger, anahtar))
            self.conn.commit()
            logger.info(f"Ayar güncellendi: {anahtar}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ayar güncelleme hatası: {str(e)}")
            return False

    def ayar_getir(self, anahtar):
        """Ayar değerini getirir"""
        try:
            self.cursor.execute('SELECT deger FROM ayarlar WHERE anahtar=?', (anahtar,))
            sonuc = self.cursor.fetchone()
            return sonuc[0] if sonuc else None
        except sqlite3.Error as e:
            logger.error(f"Ayar getirme hatası: {str(e)}")
            return None

    def tum_ayarlar(self):
        """Tüm ayarları listeler"""
        try:
            self.cursor.execute('SELECT * FROM ayarlar')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Ayar listeleme hatası: {str(e)}")
            return []

    def kullanici_ekle(self, kullanici_adi, sifre, yetki_seviyesi=1):
        """Yeni kullanıcı ekler"""
        try:
            # Şifreyi hashle
            sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
            
            self.cursor.execute('''
                INSERT INTO kullanicilar (kullanici_adi, sifre_hash, yetki_seviyesi)
                VALUES (?, ?, ?)
            ''', (kullanici_adi, sifre_hash, yetki_seviyesi))
            self.conn.commit()
            logger.info(f"Yeni kullanıcı eklendi: {kullanici_adi}")
            return True
        except sqlite3.IntegrityError:
            logger.error(f"Kullanıcı adı {kullanici_adi} zaten kayıtlı")
            return False
        except sqlite3.Error as e:
            logger.error(f"Kullanıcı ekleme hatası: {str(e)}")
            return False

    def kullanici_sifre_guncelle(self, kullanici_adi, yeni_sifre):
        """Kullanıcı şifresini günceller"""
        try:
            # Yeni şifreyi hashle
            sifre_hash = hashlib.sha256(yeni_sifre.encode()).hexdigest()
            
            self.cursor.execute('''
                UPDATE kullanicilar 
                SET sifre_hash=?
                WHERE kullanici_adi=?
            ''', (sifre_hash, kullanici_adi))
            self.conn.commit()
            logger.info(f"Kullanıcı şifresi güncellendi: {kullanici_adi}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Şifre güncelleme hatası: {str(e)}")
            return False

    def kullanici_yetki_guncelle(self, kullanici_adi, yeni_yetki_seviyesi):
        """Kullanıcı yetki seviyesini günceller"""
        try:
            self.cursor.execute('''
                UPDATE kullanicilar 
                SET yetki_seviyesi=?
                WHERE kullanici_adi=?
            ''', (yeni_yetki_seviyesi, kullanici_adi))
            self.conn.commit()
            logger.info(f"Kullanıcı yetkisi güncellendi: {kullanici_adi}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Yetki güncelleme hatası: {str(e)}")
            return False

    def kullanici_sil(self, kullanici_adi):
        """Kullanıcıyı siler"""
        try:
            self.cursor.execute('DELETE FROM kullanicilar WHERE kullanici_adi=?', (kullanici_adi,))
            self.conn.commit()
            logger.info(f"Kullanıcı silindi: {kullanici_adi}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Kullanıcı silme hatası: {str(e)}")
            return False

    def kullanici_dogrula(self, kullanici_adi, sifre):
        """Kullanıcı girişini doğrular"""
        try:
            # Şifreyi hashle
            sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()
            
            self.cursor.execute('''
                SELECT id, yetki_seviyesi 
                FROM kullanicilar 
                WHERE kullanici_adi=? AND sifre_hash=?
            ''', (kullanici_adi, sifre_hash))
            sonuc = self.cursor.fetchone()
            return sonuc if sonuc else None
        except sqlite3.Error as e:
            logger.error(f"Kullanıcı doğrulama hatası: {str(e)}")
            return None

    def tum_kullanicilar(self):
        """Tüm kullanıcıları listeler"""
        try:
            self.cursor.execute('SELECT id, kullanici_adi, yetki_seviyesi FROM kullanicilar')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Kullanıcı listeleme hatası: {str(e)}")
            return []

    def baglanti_kontrol(self):
        """Veritabanı bağlantısını kontrol eder"""
        try:
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
            return True
        except sqlite3.Error:
            return False
            
    @hata_yonetimi
    def musteri_ekle(self, tc_no, ad, soyad, telefon, email, adres):
        """Yeni müşteri ekler"""
        try:
            self.cursor.execute('''
                INSERT INTO musteriler (tc_no, ad, soyad, telefon, eposta, adres, kayit_tarihi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (tc_no, ad, soyad, telefon, email, adres, datetime.now()))
            self.conn.commit()
            logger.info(f"Yeni müşteri eklendi: {ad} {soyad}")
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.error(f"TC No {tc_no} zaten kayıtlı")
            return None
        except sqlite3.Error as e:
            logger.error(f"Müşteri ekleme hatası: {str(e)}")
            return None

    @hata_yonetimi
    def musteri_guncelle(self, musteri_id, tc_no, ad, soyad, telefon, email, adres):
        """Müşteri bilgilerini günceller"""
        try:
            self.cursor.execute('''
                UPDATE musteriler 
                SET tc_no=?, ad=?, soyad=?, telefon=?, eposta=?, adres=?
                WHERE id=?
            ''', (tc_no, ad, soyad, telefon, email, adres, musteri_id))
            self.conn.commit()
            logger.info(f"Müşteri güncellendi: {ad} {soyad}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Müşteri güncelleme hatası: {str(e)}")
            return False

    @hata_yonetimi
    def musteri_sil(self, musteri_id):
        """Müşteriyi siler"""
        try:
            # Önce müşterinin araçlarını sil
            self.cursor.execute('DELETE FROM araclar WHERE musteri_id=?', (musteri_id,))
            # Sonra müşteriyi sil
            self.cursor.execute('DELETE FROM musteriler WHERE id=?', (musteri_id,))
            self.conn.commit()
            logger.info(f"Müşteri silindi: ID {musteri_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Müşteri silme hatası: {str(e)}")
            return False

    @hata_yonetimi
    def musteri_getir(self, musteri_id):
        """Müşteri bilgilerini getirir"""
        try:
            self.cursor.execute('SELECT * FROM musteriler WHERE id=?', (musteri_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Müşteri getirme hatası: {str(e)}")
            return None

    @hata_yonetimi
    def musteri_ara(self, arama_metni):
        """Müşteri arama"""
        try:
            arama = f"%{arama_metni}%"
            self.cursor.execute('''
                SELECT * FROM musteriler 
                WHERE tc_no LIKE ? OR ad LIKE ? OR soyad LIKE ? OR telefon LIKE ?
            ''', (arama, arama, arama, arama))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Müşteri arama hatası: {str(e)}")
            return []

    @hata_yonetimi
    def tum_musteriler(self):
        """Tüm müşterileri listeler"""
        try:
            self.cursor.execute('SELECT * FROM musteriler ORDER BY ad, soyad')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Müşteri listeleme hatası: {str(e)}")
            return []

    @hata_yonetimi
    def tamir_ekle(self, musteri_id, cihaz_turu, marka, model, seri_no, sikayet, ariza, islemler, parcalar, iscilik_ucreti, parca_ucreti, toplam_ucret, durum):
        """Yeni tamir kaydı ekler"""
        try:
            self.cursor.execute("""
                INSERT INTO tamirler (
                    musteri_id, cihaz_turu, marka, model, seri_no,
                    sikayet, ariza, islemler, parcalar,
                    iscilik_ucreti, parca_ucreti, toplam_ucret, durum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                musteri_id, cihaz_turu, marka, model, seri_no,
                sikayet, ariza, islemler, parcalar,
                iscilik_ucreti, parca_ucreti, toplam_ucret, durum
            ))
            self.conn.commit()
            logger.info(f"Yeni tamir kaydı eklendi: Müşteri ID {musteri_id}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Tamir ekleme hatası: {str(e)}")
            return None

    @hata_yonetimi
    def tamir_getir(self, tamir_id):
        """Tamir kaydını getirir"""
        try:
            self.cursor.execute("""
                SELECT * FROM tamirler WHERE id = ?
            """, (tamir_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Tamir getirme hatası: {str(e)}")
            return None
            
    @hata_yonetimi
    def tamir_guncelle(self, tamir_id, musteri_id, cihaz_turu, marka, model, seri_no, sikayet, ariza, islemler, parcalar, iscilik_ucreti, parca_ucreti, toplam_ucret, durum):
        """Tamir kaydını günceller"""
        try:
            self.cursor.execute("""
                UPDATE tamirler SET
                    musteri_id = ?,
                    cihaz_turu = ?,
                    marka = ?,
                    model = ?,
                    seri_no = ?,
                    sikayet = ?,
                    ariza = ?,
                    islemler = ?,
                    parcalar = ?,
                    iscilik_ucreti = ?,
                    parca_ucreti = ?,
                    toplam_ucret = ?,
                    durum = ?,
                    guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                musteri_id, cihaz_turu, marka, model, seri_no,
                sikayet, ariza, islemler, parcalar,
                iscilik_ucreti, parca_ucreti, toplam_ucret, durum,
                tamir_id
            ))
            self.conn.commit()
            logger.info(f"Tamir kaydı güncellendi: ID {tamir_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Tamir güncelleme hatası: {str(e)}")
            return False

    @hata_yonetimi
    def tamir_durum_guncelle(self, tamir_id, durum):
        """Tamir durumunu günceller"""
        try:
            self.cursor.execute("""
                UPDATE tamirler SET
                    durum = ?,
                    guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (durum, tamir_id))
            self.conn.commit()
            logger.info(f"Tamir durumu güncellendi: ID {tamir_id} - {durum}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Tamir durum güncelleme hatası: {str(e)}")
            return False

    @hata_yonetimi
    def tamir_sil(self, tamir_id):
        """Tamir kaydını siler"""
        try:
            self.cursor.execute('DELETE FROM tamirler WHERE id = ?', (tamir_id,))
            self.conn.commit()
            logger.info(f"Tamir kaydı silindi: ID {tamir_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Tamir silme hatası: {str(e)}")
            return False

    @hata_yonetimi
    def maliyet_tahmini_ekle(self, tahmin):
        """Maliyet tahmini ekler"""
        self.cursor.execute('''
            INSERT INTO maliyet_tahminleri (tamir_id, iscilik_maliyeti, malzeme_maliyeti, toplam_maliyet, onay_durumu, aciklama, tarih)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tahmin.tamir_id, tahmin.iscilik_maliyeti, tahmin.malzeme_maliyeti, 
              tahmin.toplam_maliyet, tahmin.onay_durumu, tahmin.aciklama, tahmin.tarih))
        self.conn.commit()
        logger.info(f"Yeni maliyet tahmini eklendi: Tamir ID={tahmin.tamir_id}")
        return True

    @hata_yonetimi
    def maliyet_tahmini_guncelle(self, tahmin):
        """Maliyet tahmini günceller"""
        self.cursor.execute('''
            UPDATE maliyet_tahminleri
            SET iscilik_maliyeti=?, malzeme_maliyeti=?, toplam_maliyet=?, onay_durumu=?, aciklama=?
            WHERE id=?
        ''', (tahmin.iscilik_maliyeti, tahmin.malzeme_maliyeti, tahmin.toplam_maliyet, 
              tahmin.onay_durumu, tahmin.aciklama, tahmin.id))
        self.conn.commit()
        logger.info(f"Maliyet tahmini güncellendi: ID={tahmin.id}")
        return True

    @hata_yonetimi
    def maliyet_tahmini_sil(self, tahmin_id):
        """Maliyet tahmini siler"""
        self.cursor.execute('DELETE FROM maliyet_tahminleri WHERE id=?', (tahmin_id,))
        self.conn.commit()
        logger.info(f"Maliyet tahmini silindi: ID={tahmin_id}")
        return True

    @hata_yonetimi
    def musteri_tamir_raporu(self, baslangic, bitis, durum=None):
        """Müşteri tamir raporu oluşturur"""
        try:
            sql = '''
                SELECT 
                    m.*,
                    t.*,
                    COALESCE(t.iscilik_ucreti, 0) as iscilik_ucreti,
                    COALESCE(t.parca_ucreti, 0) as parca_ucreti,
                    COALESCE(t.iscilik_ucreti, 0) + COALESCE(t.parca_ucreti, 0) as toplam_ucret
                FROM musteriler m
                JOIN tamirler t ON m.id = t.musteri_id
                WHERE DATE(t.giris_tarihi) BETWEEN DATE(?) AND DATE(?)
            '''
            
            params = [baslangic, bitis]
            if durum:
                sql += ' AND t.durum = ?'
                params.append(durum)
                
            sql += ' ORDER BY t.giris_tarihi DESC'
            
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Müşteri tamir raporu hatası: {str(e)}")
            return []

    @hata_yonetimi
    def musteri_bazli_tamir_raporu(self, baslangic, bitis):
        """Müşteri bazlı tamir raporu oluşturur"""
        try:
            self.cursor.execute('''
                SELECT 
                    m.*,
                    COUNT(t.id) as tamir_sayisi,
                    SUM(COALESCE(t.iscilik_ucreti, 0)) as toplam_iscilik,
                    SUM(COALESCE(t.parca_ucreti, 0)) as toplam_parca,
                    SUM(COALESCE(t.iscilik_ucreti, 0) + COALESCE(t.parca_ucreti, 0)) as genel_toplam
                FROM musteriler m
                LEFT JOIN tamirler t ON m.id = t.musteri_id
                WHERE DATE(t.giris_tarihi) BETWEEN DATE(?) AND DATE(?)
                GROUP BY m.id
                HAVING tamir_sayisi > 0
                ORDER BY genel_toplam DESC
            ''', (baslangic, bitis))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Müşteri bazlı tamir raporu hatası: {str(e)}")
            return []

    @hata_yonetimi
    def maliyet_analiz_raporu(self, baslangic, bitis):
        """Maliyet analiz raporu oluşturur"""
        try:
            self.cursor.execute('''
                SELECT 
                    t.*,
                    m.ad || ' ' || m.soyad as musteri_adi,
                    COALESCE(t.iscilik_ucreti, 0) as iscilik_ucreti,
                    COALESCE(t.parca_ucreti, 0) as parca_ucreti,
                    COALESCE(t.iscilik_ucreti, 0) + COALESCE(t.parca_ucreti, 0) as toplam_ucret,
                    GROUP_CONCAT(p.parca_adi || ': ' || p.fiyat, ', ') as kullanilan_parcalar
                FROM tamirler t
                JOIN musteriler m ON t.musteri_id = m.id
                LEFT JOIN tamir_parcalari tp ON t.id = tp.tamir_id
                LEFT JOIN parcalar p ON tp.parca_id = p.id
                WHERE DATE(t.giris_tarihi) BETWEEN DATE(?) AND DATE(?)
                GROUP BY t.id
                ORDER BY toplam_ucret DESC
            ''', (baslangic, bitis))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Maliyet analiz raporu hatası: {str(e)}")
            return []

    @hata_yonetimi
    def yedek_al(self, aciklama=""):
        """Veritabanının yedeğini alır"""
        try:
            # Yedekleme klasörünü oluştur
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            # Yedek dosyasını oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.db"
            
            # Veritabanını yedekle
            shutil.copy2("tamir_atolyesi.db", backup_file)
            
            # Yedek kaydını veritabanına ekle
            self.cursor.execute("""
                INSERT INTO yedekler (tarih, dosya_adi, boyut, aciklama)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
            """, (
                backup_file.name,  # Sadece dosya adını kaydet
                os.path.getsize(backup_file),
                aciklama
            ))
            self.conn.commit()
            
            logger.info(f"Veritabanı yedeği alındı: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Yedek alma hatası: {str(e)}")
            raise Exception(f"Yedek alma hatası: {str(e)}")

    def yedek_geri_yukle(self, yedek_id):
        """Seçili yedeği geri yükler"""
        try:
            # Yedeği getir
            self.cursor.execute("SELECT dosya_adi FROM yedekler WHERE id = ?", (yedek_id,))
            yedek = self.cursor.fetchone()
            
            if not yedek:
                raise Exception("Yedek bulunamadı")
            
            backup_file = Path("backups") / yedek[0]
            if not backup_file.exists():
                raise FileNotFoundError(f"Yedek dosyası bulunamadı: {backup_file}")
            
            # Mevcut veritabanını yedekle
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = Path("backups") / f"pre_restore_{timestamp}.db"
            shutil.copy2("tamir_atolyesi.db", current_backup)
            
            # Yedeği geri yükle
            shutil.copy2(backup_file, "tamir_atolyesi.db")
            
            # Veritabanı bağlantısını yenile
            self.conn.close()
            self.conn = sqlite3.connect("tamir_atolyesi.db")
            self.cursor = self.conn.cursor()
            
            logger.info(f"Yedek geri yüklendi: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Yedek geri yükleme hatası: {str(e)}")
            raise Exception(f"Yedek geri yükleme hatası: {str(e)}")

    def yedek_sil(self, yedek_id):
        """Belirtilen yedek kaydını ve dosyasını siler"""
        try:
            self.cursor.execute("SELECT dosya_adi FROM yedekler WHERE id = ?", (yedek_id,))
            yedek = self.cursor.fetchone()
            if yedek and yedek[0]:
                backup_file = Path("backups") / yedek[0]
                if backup_file.exists():
                    backup_file.unlink()
            self.cursor.execute("DELETE FROM yedekler WHERE id = ?", (yedek_id,))
            self.conn.commit()
            logger.info(f"Yedek silindi: {yedek_id}")
            return True
        except Exception as e:
            logger.error(f"Yedek silme hatası: {str(e)}")
            raise Exception(f"Yedek silme hatası: {str(e)}")

    def eski_yedekleri_temizle(self, max_yedek=10):
        """Maksimum yedek sayısını aşan en eski yedekleri siler"""
        try:
            self.cursor.execute("SELECT id FROM yedekler ORDER BY tarih DESC")
            yedekler = [row[0] for row in self.cursor.fetchall()]
            for yedek_id in yedekler[max_yedek:]:
                self.yedek_sil(yedek_id)
        except Exception as e:
            logger.error(f"Eski yedek temizleme hatası: {str(e)}")
            # Sessiz geç

    def tum_yedeklemeler(self):
        """Tüm yedekleme kayıtlarını getirir"""
        try:
            self.cursor.execute("""
                SELECT id, tarih, dosya_adi, boyut, aciklama
                FROM yedekler
                ORDER BY tarih DESC
            """)
            yedekler = []
            for row in self.cursor.fetchall():
                yedekler.append({
                    'id': row['id'],
                    'tarih': row['tarih'],
                    'dosya_adi': row['dosya_adi'],
                    'boyut': row['boyut'],
                    'aciklama': row['aciklama']
                })
            return yedekler
        except Exception as e:
            logger.error(f"Yedekleme listesi hatası: {str(e)}")
            return []

    def tablo_olustur(self):
        """Gerekli tabloları oluşturur"""
        try:
            cursor = self.conn.cursor()
            
            # Müşteriler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS musteriler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tc_no TEXT UNIQUE,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    telefon TEXT,
                    email TEXT,
                    adres TEXT,
                    kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tamirler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tamirler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    musteri_id INTEGER NOT NULL,
                    cihaz_turu TEXT NOT NULL,
                    marka TEXT,
                    model TEXT,
                    seri_no TEXT,
                    sikayet TEXT,
                    ariza TEXT,
                    islemler TEXT,
                    parcalar TEXT,
                    iscilik_ucreti REAL DEFAULT 0,
                    parca_ucreti REAL DEFAULT 0,
                    toplam_ucret REAL DEFAULT 0,
                    durum TEXT DEFAULT 'Beklemede',
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (id)
                )
            """)
            
            # Yedekler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS yedekler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
                    dosya_adi TEXT,
                    boyut INTEGER,
                    aciklama TEXT,
                    dosya BLOB
                )
            """)
            
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Tablo oluşturma hatası: {str(e)}")

    def tamir_ara(self, arama):
        """Tamir kaydı arar"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT t.id, t.tarih, m.ad || ' ' || m.soyad as musteri, 
                       t.cihaz_turu || ' - ' || t.marka || ' ' || t.model as cihaz,
                       t.durum, t.toplam_ucret
                FROM tamirler t
                JOIN musteriler m ON t.musteri_id = m.id
                WHERE t.id LIKE ? OR
                      t.tarih LIKE ? OR
                      m.ad LIKE ? OR
                      m.soyad LIKE ? OR
                      t.cihaz_turu LIKE ? OR
                      t.marka LIKE ? OR
                      t.model LIKE ? OR
                      t.durum LIKE ?
                ORDER BY t.tarih DESC
            """, (f"%{arama}%",) * 8)
            return cursor.fetchall()
        except Exception as e:
            raise Exception(f"Tamir arama hatası: {str(e)}")

    def maliyet_tahmini_getir(self, tamir_id):
        try:
            self.cursor.execute('''
                SELECT * FROM maliyet_tahminleri WHERE tamir_id=?
            ''', (tamir_id,))
            row = self.cursor.fetchone()
            if row:
                return MaliyetTahmini(*row)
            return None
        except sqlite3.Error as e:
            print(f"Maliyet tahmini getirme hatası: {e}")
            return None

    def maliyet_tahmini_raporu(self, baslangic_tarihi, bitis_tarihi):
        try:
            self.cursor.execute('''
                SELECT mt.*, t.cihaz, t.sorun, m.ad, m.telefon
                FROM maliyet_tahminleri mt
                JOIN tamirler t ON mt.tamir_id = t.id
                JOIN musteriler m ON t.musteri_id = m.id
                WHERE mt.tarih BETWEEN ? AND ?
                ORDER BY mt.tarih DESC
            ''', (baslangic_tarihi, bitis_tarihi))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Maliyet tahmini raporu hatası: {e}")
            return []

    def tamir_gecmisi(self, musteri_id):
        try:
            self.cursor.execute('''
                SELECT * FROM tamirler
                WHERE musteri_id=?
                ORDER BY tarih DESC
            ''', (musteri_id,))
            return [Tamir(*row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Tamir geçmişi hatası: {e}")
            return []

    def arac_ekle(self, musteri_id, plaka, marka, model, yil, renk, sasi_no):
        """Yeni araç ekler"""
        try:
            self.cursor.execute('''
                INSERT INTO araclar (musteri_id, plaka, marka, model, yil, renk, sasi_no)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (musteri_id, plaka, marka, model, yil, renk, sasi_no))
            self.conn.commit()
            logger.info(f"Yeni araç eklendi: {plaka}")
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.error(f"Plaka {plaka} zaten kayıtlı")
            return None
        except sqlite3.Error as e:
            logger.error(f"Araç ekleme hatası: {str(e)}")
            return None

    def arac_guncelle(self, arac_id, plaka, marka, model, yil, renk, sasi_no):
        """Araç bilgilerini günceller"""
        try:
            self.cursor.execute('''
                UPDATE araclar 
                SET plaka=?, marka=?, model=?, yil=?, renk=?, sasi_no=?
                WHERE id=?
            ''', (plaka, marka, model, yil, renk, sasi_no, arac_id))
            self.conn.commit()
            logger.info(f"Araç güncellendi: {plaka}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Araç güncelleme hatası: {str(e)}")
            return False

    def arac_sil(self, arac_id):
        """Aracı siler"""
        try:
            # Önce aracın onarımlarını sil
            self.cursor.execute('DELETE FROM onarimlar WHERE arac_id=?', (arac_id,))
            # Sonra aracı sil
            self.cursor.execute('DELETE FROM araclar WHERE id=?', (arac_id,))
            self.conn.commit()
            logger.info(f"Araç silindi: ID {arac_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Araç silme hatası: {str(e)}")
            return False

    def arac_getir(self, arac_id):
        """ID'ye göre araç bilgilerini getirir"""
        try:
            self.cursor.execute("""
                SELECT * FROM araclar WHERE id = ?
            """, (arac_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Araç getirme hatası: {str(e)}")
            return None

    def arac_ara(self, arama_metni):
        """Araç arama"""
        try:
            arama = f"%{arama_metni}%"
            self.cursor.execute('''
                SELECT a.*, m.ad, m.soyad 
                FROM araclar a 
                JOIN musteriler m ON a.musteri_id = m.id 
                WHERE a.plaka LIKE ? OR a.marka LIKE ? OR a.model LIKE ? OR a.sasi_no LIKE ?
            ''', (arama, arama, arama, arama))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Araç arama hatası: {str(e)}")
            return []

    def musteri_araclari(self, musteri_id):
        """Müşterinin araçlarını listeler"""
        try:
            self.cursor.execute('''
                SELECT * FROM araclar 
                WHERE musteri_id=? 
                ORDER BY marka, model
            ''', (musteri_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Müşteri araçları listeleme hatası: {str(e)}")
            return []

    def tum_araclar(self):
        """Tüm araçları listeler"""
        try:
            self.cursor.execute('''
                SELECT a.*, m.ad, m.soyad 
                FROM araclar a 
                JOIN musteriler m ON a.musteri_id = m.id 
                ORDER BY a.marka, a.model
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Araç listeleme hatası: {str(e)}")
            return []

    def onarim_ekle(self, arac_id, aciklama, yapilan_islemler, parcalar, iscilik_ucreti, parca_ucreti, toplam_ucret, durum="Beklemede"):
        """Yeni onarım kaydı ekler"""
        try:
            self.cursor.execute('''
                INSERT INTO onarimlar (
                    arac_id, aciklama, yapilan_islemler, parcalar, 
                    iscilik_ucreti, parca_ucreti, toplam_ucret,
                    durum, baslangic_tarihi
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (arac_id, aciklama, yapilan_islemler, parcalar, 
                 iscilik_ucreti, parca_ucreti, toplam_ucret,
                 durum, datetime.now()))
            self.conn.commit()
            logger.info(f"Yeni onarım kaydı eklendi: Araç ID {arac_id}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Onarım ekleme hatası: {str(e)}")
            return None

    def onarim_guncelle(self, onarim_id, aciklama, yapilan_islemler, parcalar, 
                       iscilik_ucreti, parca_ucreti, toplam_ucret, durum):
        """Onarım kaydını günceller"""
        try:
            self.cursor.execute('''
                UPDATE onarimlar 
                SET aciklama=?, yapilan_islemler=?, parcalar=?,
                    iscilik_ucreti=?, parca_ucreti=?, toplam_ucret=?,
                    durum=?, guncelleme_tarihi=?
                WHERE id=?
            ''', (aciklama, yapilan_islemler, parcalar,
                 iscilik_ucreti, parca_ucreti, toplam_ucret,
                 durum, datetime.now(), onarim_id))
            self.conn.commit()
            logger.info(f"Onarım kaydı güncellendi: ID {onarim_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Onarım güncelleme hatası: {str(e)}")
            return False

    def onarim_durum_guncelle(self, onarim_id, durum):
        """Onarım durumunu günceller"""
        try:
            self.cursor.execute('''
                UPDATE onarimlar 
                SET durum=?, guncelleme_tarihi=?
                WHERE id=?
            ''', (durum, datetime.now(), onarim_id))
            
            if durum == "Tamamlandı":
                self.cursor.execute('''
                    UPDATE onarimlar 
                    SET bitis_tarihi=?
                    WHERE id=?
                ''', (datetime.now(), onarim_id))
                
            self.conn.commit()
            logger.info(f"Onarım durumu güncellendi: ID {onarim_id} - {durum}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Onarım durum güncelleme hatası: {str(e)}")
            return False

    def onarim_sil(self, onarim_id):
        """Onarım kaydını siler"""
        try:
            self.cursor.execute('DELETE FROM onarimlar WHERE id=?', (onarim_id,))
            self.conn.commit()
            logger.info(f"Onarım kaydı silindi: ID {onarim_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Onarım silme hatası: {str(e)}")
            return False

    def onarim_getir(self, onarim_id):
        """Onarım kaydını getirir"""
        try:
            self.cursor.execute('''
                SELECT o.*, a.plaka, m.ad, m.soyad 
                FROM onarimlar o
                JOIN araclar a ON o.arac_id = a.id
                JOIN musteriler m ON a.musteri_id = m.id
                WHERE o.id=?
            ''', (onarim_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Onarım getirme hatası: {str(e)}")
            return None

    def arac_onarimlari(self, arac_id):
        """Aracın onarım geçmişini listeler"""
        try:
            self.cursor.execute('''
                SELECT * FROM onarimlar 
                WHERE arac_id=? 
                ORDER BY baslangic_tarihi DESC
            ''', (arac_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Araç onarımları listeleme hatası: {str(e)}")
            return []

    def aktif_onarimlar(self):
        """Devam eden onarımları listeler"""
        try:
            self.cursor.execute('''
                SELECT o.*, a.plaka, m.ad, m.soyad 
                FROM onarimlar o
                JOIN araclar a ON o.arac_id = a.id
                JOIN musteriler m ON a.musteri_id = m.id
                WHERE o.durum != 'Tamamlandı'
                ORDER BY o.baslangic_tarihi DESC
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Aktif onarımlar listeleme hatası: {str(e)}")
            return []

    def tamamlanan_onarimlar(self, baslangic_tarih=None, bitis_tarih=None):
        """Tamamlanan onarımları listeler"""
        try:
            if baslangic_tarih and bitis_tarih:
                self.cursor.execute('''
                    SELECT o.*, a.plaka, m.ad, m.soyad 
                    FROM onarimlar o
                    JOIN araclar a ON o.arac_id = a.id
                    JOIN musteriler m ON a.musteri_id = m.id
                    WHERE o.durum = 'Tamamlandı'
                    AND o.bitis_tarihi BETWEEN ? AND ?
                    ORDER BY o.bitis_tarihi DESC
                ''', (baslangic_tarih, bitis_tarih))
            else:
                self.cursor.execute('''
                    SELECT o.*, a.plaka, m.ad, m.soyad 
                    FROM onarimlar o
                    JOIN araclar a ON o.arac_id = a.id
                    JOIN musteriler m ON a.musteri_id = m.id
                    WHERE o.durum = 'Tamamlandı'
                    ORDER BY o.bitis_tarihi DESC
                ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Tamamlanan onarımlar listeleme hatası: {str(e)}")
            return []

    def tum_onarimlar(self):
        """Tüm onarımları listeler"""
        try:
            self.cursor.execute('''
                SELECT o.*, a.plaka, m.ad || ' ' || m.soyad as musteri_adi
                FROM onarimlar o
                JOIN araclar a ON o.arac_id = a.id
                JOIN musteriler m ON a.musteri_id = m.id
                ORDER BY o.giris_tarihi DESC
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Onarım listesi getirme hatası: {str(e)}")
            return []

    @hata_yonetimi
    def musteri_listesi(self):
        """Tüm müşterileri listeler"""
        try:
            self.cursor.execute('''
                SELECT id, ad, soyad, telefon, eposta, adres
                FROM musteriler
                ORDER BY ad, soyad
            ''')
            musteriler = self.cursor.fetchall()
            return [
                {
                    'id': m[0],
                    'ad': m[1],
                    'soyad': m[2],
                    'telefon': m[3],
                    'eposta': m[4],
                    'adres': m[5]
                }
                for m in musteriler
            ]
        except sqlite3.Error as e:
            logger.error(f"Müşteri listeleme hatası: {str(e)}")
            return []

    def tamir_listesi_getir(self):
        """Tüm tamir kayıtlarını getirir"""
        try:
            self.cursor.execute("""
                SELECT 
                    t.id,
                    a.plaka,
                    a.marka,
                    t.sorun,
                    t.durum,
                    t.giris_tarihi
                FROM tamirler t
                JOIN araclar a ON t.arac_id = a.id
                ORDER BY t.giris_tarihi DESC
            """)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Tamir listesi getirme hatası: {str(e)}")
            return []

    def arac_bul(self, plaka):
        """Plakaya göre araç bilgilerini getirir"""
        try:
            self.cursor.execute("""
                SELECT * FROM araclar WHERE plaka = ?
            """, (plaka,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Araç arama hatası: {str(e)}")
            return None
            
    def aylik_rapor(self, ay, yil):
        """Aylık rapor oluşturur"""
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as toplam_tamir,
                    AVG(JULIANDAY(guncelleme_tarihi) - JULIANDAY(giris_tarihi)) as ortalama_sure,
                    SUM(toplam_ucret) as toplam_gelir,
                    SUM(iscilik_ucreti) as toplam_iscilik,
                    SUM(parca_ucreti) as toplam_parca,
                    COUNT(CASE WHEN durum = 'Tamamlandı' THEN 1 END) as tamamlanan,
                    COUNT(CASE WHEN durum != 'Tamamlandı' THEN 1 END) as devam_eden
                FROM tamirler
                WHERE strftime('%m', giris_tarihi) = ? AND strftime('%Y', giris_tarihi) = ?
            ''', (f"{ay:02d}", str(yil)))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    'toplam_tamir': row[0],
                    'ortalama_sure': row[1] if row[1] else 0,
                    'toplam_gelir': row[2] if row[2] else 0,
                    'toplam_iscilik': row[3] if row[3] else 0,
                    'toplam_parca': row[4] if row[4] else 0,
                    'tamamlanan': row[5],
                    'devam_eden': row[6]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Aylık rapor hatası: {str(e)}")
            return None
            
    def yillik_rapor(self, yil):
        """Yıllık rapor oluşturur"""
        try:
            aylik_veriler = []
            for ay in range(1, 13):
                self.cursor.execute('''
                    SELECT 
                        COUNT(*) as tamir_sayisi,
                        AVG(JULIANDAY(guncelleme_tarihi) - JULIANDAY(giris_tarihi)) as ortalama_sure,
                        SUM(toplam_ucret) as toplam_gelir,
                        SUM(iscilik_ucreti) as toplam_iscilik,
                        SUM(parca_ucreti) as toplam_parca,
                        COUNT(CASE WHEN durum = 'Tamamlandı' THEN 1 END) as tamamlanan,
                        COUNT(CASE WHEN durum != 'Tamamlandı' THEN 1 END) as devam_eden
                    FROM tamirler
                    WHERE strftime('%m', giris_tarihi) = ? AND strftime('%Y', giris_tarihi) = ?
                ''', (f"{ay:02d}", str(yil)))
                
                row = self.cursor.fetchone()
                aylik_veriler.append({
                    'ay': ay,
                    'tamir_sayisi': row[0],
                    'ortalama_sure': row[1] if row[1] else 0,
                    'toplam_gelir': row[2] if row[2] else 0,
                    'toplam_iscilik': row[3] if row[3] else 0,
                    'toplam_parca': row[4] if row[4] else 0,
                    'tamamlanan': row[5],
                    'devam_eden': row[6]
                })
                
            return aylik_veriler
        except sqlite3.Error as e:
            logger.error(f"Yıllık rapor hatası: {str(e)}")
            return []
            
    def gelir_raporu(self, baslangic, bitis):
        """Gelir raporu oluşturur"""
        try:
            self.cursor.execute('''
                SELECT 
                    SUM(iscilik_ucreti) as toplam_iscilik,
                    SUM(parca_ucreti) as toplam_parca,
                    SUM(toplam_ucret) as genel_toplam,
                    COUNT(*) as tamir_sayisi,
                    AVG(toplam_ucret) as ortalama_ucret
                FROM tamirler
                WHERE date(giris_tarihi) BETWEEN date(?) AND date(?)
            ''', (baslangic, bitis))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    'toplam_iscilik': row[0] if row[0] else 0,
                    'toplam_parca': row[1] if row[1] else 0,
                    'genel_toplam': row[2] if row[2] else 0,
                    'tamir_sayisi': row[3] if row[3] else 0,
                    'ortalama_ucret': row[4] if row[4] else 0
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Gelir raporu hatası: {str(e)}")
            return None
            
    def tamir_raporu(self, baslangic, bitis, durum=None):
        """Tamir raporu oluşturur"""
        try:
            if durum:
                self.cursor.execute('''
                    SELECT 
                        t.*,
                        m.ad || ' ' || m.soyad as musteri_adi
                    FROM tamirler t
                    JOIN musteriler m ON t.musteri_id = m.id
                    WHERE t.giris_tarihi BETWEEN ? AND ?
                    AND t.durum = ?
                    ORDER BY t.giris_tarihi DESC
                ''', (baslangic, bitis, durum))
            else:
                self.cursor.execute('''
                    SELECT 
                        t.*,
                        m.ad || ' ' || m.soyad as musteri_adi
                    FROM tamirler t
                    JOIN musteriler m ON t.musteri_id = m.id
                    WHERE t.giris_tarihi BETWEEN ? AND ?
                    ORDER BY t.giris_tarihi DESC
                ''', (baslangic, bitis))
            
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Tamir raporu hatası: {str(e)}")
            return []

    def tum_musteri_sayisi(self):
        """Toplam müşteri sayısını döndürür"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM musteriler')
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Müşteri sayısı hatası: {str(e)}")
            return 0

    def yillik_gelir(self):
        """Bu yılın toplam gelirini döndürür"""
        try:
            self.cursor.execute('''
                SELECT SUM(toplam_ucret)
                FROM tamirler
                WHERE strftime('%Y', tarih) = strftime('%Y', 'now')
            ''')
            sonuc = self.cursor.fetchone()[0]
            return float(sonuc) if sonuc else 0.0
        except sqlite3.Error as e:
            logger.error(f"Yıllık gelir hesaplama hatası: {str(e)}")
            return 0.0

    def tum_tamirler(self):
        """Tüm tamir kayıtlarını getirir"""
        try:
            self.cursor.execute('''
                SELECT 
                    t.id,
                    t.giris_tarihi,
                    m.ad,
                    m.soyad,
                    t.cihaz_turu || ' ' || t.marka || ' ' || t.model as cihaz,
                    t.durum,
                    t.toplam_ucret
                FROM tamirler t
                JOIN musteriler m ON t.musteri_id = m.id
                ORDER BY t.giris_tarihi DESC
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Tamir listesi getirme hatası: {str(e)}")
            return []

    @hata_yonetimi
    def tamir_tamamla(self, tamir_id):
        """Belirtilen tamir kaydını tamamlandı olarak işaretler"""
        return self.tamir_durum_guncelle(tamir_id, "Tamamlandı")

    def giris_tarihi_alani_ekle(self):
        """tamirler tablosuna giris_tarihi alanı ekler (varsa hata vermez)"""
        try:
            self.cursor.execute("ALTER TABLE tamirler ADD COLUMN giris_tarihi DATETIME DEFAULT (datetime('now','localtime'));")
            self.conn.commit()
        except Exception as e:
            if 'duplicate column name' in str(e) or 'already exists' in str(e):
                pass  # Zaten ekli ise hata verme
            else:
                raise

    def test_tamirlerini_sil(self):
        """Test verisi olarak eklenen tamir ve müşterileri siler (ad TestAd ile başlayanlar)"""
        try:
            self.cursor.execute("DELETE FROM tamirler WHERE musteri_id IN (SELECT id FROM musteriler WHERE ad LIKE 'TestAd%')")
            self.cursor.execute("DELETE FROM musteriler WHERE ad LIKE 'TestAd%'")
            self.conn.commit()
        except Exception as e:
            raise 