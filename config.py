import os
from pathlib import Path
import json

# Ana dizin yolları
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"
CONFIG_FILE = DATA_DIR / "email_config.json"

# Dizinleri oluştur
for directory in [DATA_DIR, BACKUP_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Veritabanı ayarları
DB_NAME = "tamir_atolyesi.db"
DB_PATH = DATA_DIR / DB_NAME

# Rapor ayarları
REPORT_DIR = Path.home() / "Documents" / "TamirAtolyesiRaporlari"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Log ayarları
LOG_FILE = LOG_DIR / "tamir_atolyesi.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Yedekleme ayarları
BACKUP_INTERVAL = 24  # saat
MAX_BACKUPS = 5  # maksimum yedek sayısı
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "sender_email": "",
    "sender_password": "",  # Gmail için uygulama şifresi
    "receiver_email": "",
    "backup_time": "23:00"  # Yedekleme saati (24 saat formatında)
}

# E-posta ayarlarını yükle veya oluştur
def load_email_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return EMAIL_CONFIG

def save_email_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Uygulama ayarları
APP_NAME = "Tamir Atölyesi Yönetim Sistemi"
APP_VERSION = "1.0.0"

# E-posta ayarlarını yükle
EMAIL_CONFIG = load_email_config() 