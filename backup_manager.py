import smtplib
import threading
import schedule
import time
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
import logging
from config import EMAIL_CONFIG, DB_PATH, BACKUP_DIR, BACKUP_CONFIG, MAX_BACKUPS, BACKUP_INTERVAL
from utils import veritabani_yedekle, logger, dosya_boyutu_formatla
import os
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.application import MIMEApplication
from typing import List, Optional

logger = logging.getLogger(__name__)

class YedekYoneticisi:
    def __init__(self):
        self.email_config = EMAIL_CONFIG
        self.db_path = DB_PATH
        self.backup_dir = BACKUP_DIR
        self.backup_interval = BACKUP_CONFIG["backup_interval"]
        self.max_backups = BACKUP_CONFIG["max_backups"]
        self.running = False
        self.thread = None
        self.stop_flag = False
        self.backup_thread = None
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def email_ayarlarini_guncelle(self, sender_email, sender_password, receiver_email, backup_time):
        """E-posta ayarlarını günceller"""
        self.email_config.update({
            "sender_email": sender_email,
            "sender_password": sender_password,
            "receiver_email": receiver_email,
            "backup_time": backup_time
        })
        from config import save_email_config
        save_email_config(self.email_config)
        logger.info("E-posta ayarları güncellendi")
    
    def test_email_connection(self):
        """E-posta bağlantısını test eder"""
        try:
            with smtplib.SMTP_SSL(self.email_config["smtp_server"], self.email_config["smtp_port"]) as smtp:
                smtp.login(self.email_config["sender_email"], self.email_config["sender_password"])
            return True
        except Exception as e:
            logger.error(f"E-posta bağlantı hatası: {str(e)}")
            return False
    
    def yedek_al(self):
        """Veritabanının yedeğini alır"""
        try:
            # Yedek dosya adını oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.db"
            
            # Veritabanını yedekle
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"Yedek oluşturuldu: {backup_file}")
            
            # Eski yedekleri temizle
            self.eski_yedekleri_temizle()
            
            return str(backup_file)
        except Exception as e:
            logger.error(f"Yedekleme hatası: {str(e)}")
            return None
            
    def eski_yedekleri_temizle(self):
        """Eski yedek dosyalarını temizler"""
        try:
            # Tüm yedek dosyalarını al
            backups = sorted(self.backup_dir.glob("backup_*.db"))
            
            # Maksimum sayıdan fazla yedek varsa en eskileri sil
            while len(backups) > MAX_BACKUPS:
                oldest = backups.pop(0)
                oldest.unlink()
                logger.info(f"Eski yedek silindi: {oldest}")
        except Exception as e:
            logger.error(f"Yedek temizleme hatası: {str(e)}")
    
    def email_gonder(self, backup_file, email_config):
        """Yedek dosyasını e-posta ile gönderir"""
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['email']
            msg['To'] = email_config['email']
            msg['Subject'] = EMAIL_CONFIG['SUBJECT']
            
            msg.attach(MIMEText(EMAIL_CONFIG['BODY'], 'plain'))
            
            # Dosyayı ekle
            with open(backup_file, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 
                          f'attachment; filename="{Path(backup_file).name}"')
            msg.attach(part)
            
            # E-postayı gönder
            server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Yedek e-posta ile gönderildi")
            return True
        except Exception as e:
            logger.error(f"E-posta gönderme hatası: {str(e)}")
            return False
    
    def yedekleme_dongusu(self):
        """Otomatik yedekleme döngüsü"""
        while self.running:
            try:
                backup_file = self.yedek_al()
                if backup_file:
                    logger.info("Otomatik yedek alındı")
                time.sleep(BACKUP_INTERVAL * 3600)  # Saat -> saniye
            except Exception as e:
                logger.error(f"Yedekleme döngüsü hatası: {str(e)}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle
    
    def start_scheduler(self):
        """Otomatik yedekleme zamanlayıcısını başlatır"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.yedekleme_dongusu)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Otomatik yedekleme başlatıldı")
    
    def stop_scheduler(self):
        """Otomatik yedekleme zamanlayıcısını durdurur"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logger.info("Otomatik yedekleme durduruldu")
    
    def _schedule_runner(self):
        """Zamanlayıcı döngüsü"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
    
    def _backup_scheduler(self):
        """Yedekleme zamanlayıcı döngüsü"""
        while not self.stop_flag:
            try:
                self.create_backup()
                # Bir sonraki yedekleme için bekle
                for _ in range(int(self.backup_interval * 3600)):
                    if self.stop_flag:
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Otomatik yedekleme sırasında hata: {str(e)}")
                time.sleep(300)  # Hata durumunda 5 dakika bekle
    
    def create_backup(self):
        """Veritabanının yedeğini oluşturur"""
        try:
            # Yedek dosya adını oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.db"
            
            # Veritabanını yedekle
            shutil.copy2("data/tamir_atolyesi.db", backup_file)
            
            # Eski yedekleri temizle
            self._cleanup_old_backups()
            
            logger.info(f"Yedekleme başarıyla oluşturuldu: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Yedekleme oluşturulurken hata: {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """Eski yedekleri temizler"""
        try:
            # Yedek dosyalarını tarihe göre sırala
            backups = sorted(
                self.backup_dir.glob("backup_*.db"),
                key=lambda x: x.stat().st_mtime
            )
            
            # Maksimum yedek sayısını aşan dosyaları sil
            while len(backups) > self.max_backups:
                oldest_backup = backups.pop(0)
                oldest_backup.unlink()
                logger.info(f"Eski yedek silindi: {oldest_backup}")
                
        except Exception as e:
            logger.error(f"Eski yedekler temizlenirken hata: {str(e)}")
    
    def restore_backup(self, backup_file):
        """Seçilen yedeği geri yükler"""
        try:
            if not backup_file.exists():
                raise FileNotFoundError(f"Yedek dosyası bulunamadı: {backup_file}")
            
            # Mevcut veritabanını yedekle
            current_backup = self.create_backup()
            if not current_backup:
                raise Exception("Mevcut durumun yedeği alınamadı")
            
            # Yedeği geri yükle
            shutil.copy2(backup_file, "data/tamir_atolyesi.db")
            logger.info(f"Yedek başarıyla geri yüklendi: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Yedek geri yüklenirken hata: {str(e)}")
            return False 

class YedeklemeYonetici:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.db_path = DB_PATH
        self.max_backups = MAX_BACKUPS
        self.backup_interval = BACKUP_INTERVAL
        self.running = False
        self.thread = None
        
        # Yedekleme dizinini oluştur
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Yedekleme yöneticisi başlatıldı")
    
    def yedek_al(self, aciklama=""):
        """Veritabanının yedeğini alır"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.db"
            
            # Veritabanını yedekle
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"Yedek oluşturuldu: {backup_file}")
            
            # Eski yedekleri temizle
            self.eski_yedekleri_temizle()
            
            return str(backup_file)
        except Exception as e:
            logger.error(f"Yedekleme hatası: {str(e)}")
            return None
    
    def eski_yedekleri_temizle(self):
        """Eski yedek dosyalarını temizler"""
        try:
            yedekler = sorted(
                self.backup_dir.glob("backup_*.db"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            while len(yedekler) > self.max_backups:
                silinecek = yedekler.pop()
                silinecek.unlink()
                logger.info(f"Eski yedek silindi: {silinecek}")
        except Exception as e:
            logger.error(f"Yedek temizleme hatası: {str(e)}")
    
    def yedekleri_listele(self):
        """Mevcut yedekleri listeler"""
        try:
            return sorted(
                self.backup_dir.glob("backup_*.db"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
        except Exception as e:
            logger.error(f"Yedekleri listeleme hatası: {str(e)}")
            return []
    
    def yedek_geri_yukle(self, yedek_dosyasi):
        """Seçilen yedeği geri yükler"""
        try:
            if not yedek_dosyasi.exists():
                raise FileNotFoundError(f"Yedek dosyası bulunamadı: {yedek_dosyasi}")
            
            # Mevcut durumun yedeğini al
            gecici_yedek = self.yedek_al("Geri yükleme öncesi otomatik yedek")
            if not gecici_yedek:
                raise Exception("Mevcut durumun yedeği alınamadı")
            
            # Yedeği geri yükle
            shutil.copy2(yedek_dosyasi, self.db_path)
            logger.info(f"Yedek başarıyla geri yüklendi: {yedek_dosyasi}")
            return True
        except Exception as e:
            logger.error(f"Yedek geri yükleme hatası: {str(e)}")
            return False
    
    def otomatik_yedeklemeyi_baslat(self):
        """Otomatik yedekleme işlemini başlatır"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._yedekleme_dongusu)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Otomatik yedekleme başlatıldı")
    
    def otomatik_yedeklemeyi_durdur(self):
        """Otomatik yedekleme işlemini durdurur"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logger.info("Otomatik yedekleme durduruldu")
    
    def _yedekleme_dongusu(self):
        """Yedekleme döngüsü"""
        while self.running:
            try:
                self.yedek_al("Otomatik yedekleme")
                time.sleep(self.backup_interval)
            except Exception as e:
                logger.error(f"Otomatik yedekleme hatası: {str(e)}")
                time.sleep(300)  # Hata durumunda 5 dakika bekle 