import sqlite3
from datetime import datetime
from pathlib import Path
from config import DB_PATH
from utils import veritabani_yedekle, veritabani_baglantisi_kontrol_et, hata_yonetimi, logger
from models import Musteri, Tamir, MaliyetTahmini

class VeritabaniYonetici:
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = None
        self.cursor = None
        self.baglanti_kur()
        self.tablolari_olustur()

    def baglanti_kur(self):
        """Veritabanı bağlantısını kurar"""
        try:
            if not veritabani_baglantisi_kontrol_et(self.db_path):
                raise Exception("Veritabanı bağlantısı kurulamadı")
            
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info("Veritabanı bağlantısı başarıyla kuruldu")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
            raise

    def tablolari_olustur(self):
        try:
            # Müşteriler tablosu
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS musteriler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    telefon TEXT NOT NULL,
                    email TEXT,
                    adres TEXT
                )
            ''')

            # Tamirler tablosu
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tamirler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    musteri_id INTEGER NOT NULL,
                    cihaz TEXT NOT NULL,
                    sorun TEXT NOT NULL,
                    tarih TEXT NOT NULL,
                    maliyet REAL,
                    durum TEXT DEFAULT 'Açık',
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (id)
                )
            ''')

            # Maliyet tahminleri tablosu
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS maliyet_tahminleri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tamir_id INTEGER NOT NULL,
                    iscilik_maliyeti REAL NOT NULL,
                    malzeme_maliyeti REAL NOT NULL,
                    toplam_maliyet REAL NOT NULL,
                    onay_durumu TEXT DEFAULT 'Beklemede',
                    aciklama TEXT,
                    tarih TEXT NOT NULL,
                    FOREIGN KEY (tamir_id) REFERENCES tamirler (id)
                )
            ''')

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Tablo oluşturma hatası: {e}")
            raise

    @hata_yonetimi
    def musteri_ekle(self, musteri):
        """Müşteri ekler"""
        self.cursor.execute('''
            INSERT INTO musteriler (ad, soyad, telefon, email, adres)
            VALUES (?, ?, ?, ?, ?)
        ''', (musteri.ad, musteri.soyad, musteri.telefon, musteri.email, musteri.adres))
        self.conn.commit()
        logger.info(f"Yeni müşteri eklendi: {musteri.ad} {musteri.soyad}")
        return True

    @hata_yonetimi
    def musteri_guncelle(self, musteri):
        """Müşteri günceller"""
        self.cursor.execute('''
            UPDATE musteriler
            SET ad=?, soyad=?, telefon=?, email=?, adres=?
            WHERE id=?
        ''', (musteri.ad, musteri.soyad, musteri.telefon, musteri.email, musteri.adres, musteri.id))
        self.conn.commit()
        logger.info(f"Müşteri güncellendi: {musteri.ad} {musteri.soyad}")
        return True

    @hata_yonetimi
    def musteri_sil(self, musteri_id):
        """Müşteri siler"""
        self.cursor.execute('DELETE FROM musteriler WHERE id=?', (musteri_id,))
        self.conn.commit()
        logger.info(f"Müşteri silindi: ID={musteri_id}")
        return True

    @hata_yonetimi
    def musteri_ara(self, anahtar_kelime):
        """Müşteri arar"""
        self.cursor.execute('''
            SELECT * FROM musteriler
            WHERE ad LIKE ? OR soyad LIKE ? OR telefon LIKE ?
        ''', (f'%{anahtar_kelime}%', f'%{anahtar_kelime}%', f'%{anahtar_kelime}%'))
        sonuclar = self.cursor.fetchall()
        # Tuple'ları Musteri nesnelerine dönüştür
        return [Musteri(*row) for row in sonuclar]

    @hata_yonetimi
    def tamir_ekle(self, tamir):
        """Tamir ekler"""
        self.cursor.execute('''
            INSERT INTO tamirler (musteri_id, cihaz, sorun, tarih, maliyet, durum)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tamir.musteri_id, tamir.cihaz, tamir.sorun, tamir.tarih, tamir.maliyet, tamir.durum))
        self.conn.commit()
        logger.info(f"Yeni tamir eklendi: Cihaz={tamir.cihaz}, Müşteri ID={tamir.musteri_id}")
        return True

    @hata_yonetimi
    def tamir_guncelle(self, tamir):
        """Tamir günceller"""
        self.cursor.execute('''
            UPDATE tamirler
            SET cihaz=?, sorun=?, maliyet=?, durum=?
            WHERE id=?
        ''', (tamir.cihaz, tamir.sorun, tamir.maliyet, tamir.durum, tamir.id))
        self.conn.commit()
        logger.info(f"Tamir güncellendi: ID={tamir.id}")
        return True

    @hata_yonetimi
    def tamir_sil(self, tamir_id):
        """Tamir siler"""
        self.cursor.execute('DELETE FROM tamirler WHERE id=?', (tamir_id,))
        self.conn.commit()
        logger.info(f"Tamir silindi: ID={tamir_id}")
        return True

    @hata_yonetimi
    def tamir_ara(self, anahtar_kelime):
        """Tamir arar"""
        self.cursor.execute('''
            SELECT t.*, m.ad, m.soyad
            FROM tamirler t
            JOIN musteriler m ON t.musteri_id = m.id
            WHERE t.cihaz LIKE ? OR t.sorun LIKE ? OR m.ad LIKE ? OR m.soyad LIKE ?
        ''', (f'%{anahtar_kelime}%', f'%{anahtar_kelime}%', f'%{anahtar_kelime}%', f'%{anahtar_kelime}%'))
        return self.cursor.fetchall()

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
    def musteri_tamir_raporu(self, baslangic, bitis):
        """Müşteri ve tamir raporu oluşturur"""
        self.cursor.execute('''
            SELECT m.*, t.*
            FROM musteriler m
            JOIN tamirler t ON m.id = t.musteri_id
            WHERE t.tarih BETWEEN ? AND ?
            ORDER BY t.tarih DESC
        ''', (baslangic, bitis))
        return self.cursor.fetchall()

    @hata_yonetimi
    def yedek_al(self):
        """Veritabanı yedeği alır"""
        return veritabani_yedekle(self.db_path)

    def __del__(self):
        """Bağlantıyı kapatır"""
        if self.conn:
            self.conn.close()
            logger.info("Veritabanı bağlantısı kapatıldı")

    def aylik_rapor(self, ay, yil):
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as toplam_islem,
                    SUM(maliyet) as toplam_gelir,
                    SUM(CASE WHEN durum = 'Tamamlandı' THEN 1 ELSE 0 END) as tamamlanan,
                    SUM(CASE WHEN durum = 'Açık' THEN 1 ELSE 0 END) as acik
                FROM tamirler
                WHERE strftime('%m', tarih) = ? AND strftime('%Y', tarih) = ?
            ''', (f"{ay:02d}", str(yil)))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Rapor oluşturma hatası: {e}")
            return None

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