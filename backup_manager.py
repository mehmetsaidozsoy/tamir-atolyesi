import smtplib
import threading
import schedule
import time
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
import logging
from config import EMAIL_CONFIG, DB_PATH, BACKUP_DIR
from utils import veritabani_yedekle, logger

class YedekYoneticisi:
    def __init__(self):
        self.email_config = EMAIL_CONFIG
        self.db_path = DB_PATH
        self.backup_dir = BACKUP_DIR
        self.running = False
        self.thread = None
    
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
    
    def yedegi_gonder(self):
        """Veritabanı yedeğini e-posta ile gönderir"""
        try:
            # Önce yedeği al
            yedek_dosya = self.backup_dir / f"tamir_atolyesi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            veritabani_yedekle(self.db_path)
            
            # E-posta oluştur
            msg = EmailMessage()
            msg['Subject'] = f'Tamir Atölyesi Veritabanı Yedeği - {datetime.now().strftime("%d.%m.%Y")}'
            msg['From'] = self.email_config["sender_email"]
            msg['To'] = self.email_config["receiver_email"]
            msg.set_content('Otomatik veritabanı yedeği ektedir.')
            
            # Yedeği ekle
            with open(yedek_dosya, 'rb') as f:
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='octet-stream',
                    filename=yedek_dosya.name
                )
            
            # E-postayı gönder
            with smtplib.SMTP_SSL(self.email_config["smtp_server"], self.email_config["smtp_port"]) as smtp:
                smtp.login(self.email_config["sender_email"], self.email_config["sender_password"])
                smtp.send_message(msg)
            
            logger.info(f"Veritabanı yedeği e-posta ile gönderildi: {self.email_config['receiver_email']}")
            return True
        except Exception as e:
            logger.error(f"Yedek gönderme hatası: {str(e)}")
            return False
    
    def _schedule_runner(self):
        """Zamanlayıcı döngüsü"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
    
    def start_scheduler(self):
        """Zamanlayıcıyı başlatır"""
        if not self.running:
            self.running = True
            # Günlük yedekleme zamanını ayarla
            schedule.every().day.at(self.email_config["backup_time"]).do(self.yedegi_gonder)
            # Arka planda çalıştır
            self.thread = threading.Thread(target=self._schedule_runner)
            self.thread.daemon = True  # Ana program kapanınca bu da kapansın
            self.thread.start()
            logger.info("Otomatik yedekleme zamanlayıcısı başlatıldı")
    
    def stop_scheduler(self):
        """Zamanlayıcıyı durdurur"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            schedule.clear()
            logger.info("Otomatik yedekleme zamanlayıcısı durduruldu") 