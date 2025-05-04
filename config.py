import os
from pathlib import Path
import json
import logging

# Uygulama dizini
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups"
ICONS_DIR = APP_DIR / "icons"
DB_PATH = DATA_DIR / "database.db"
CONFIG_FILE = DATA_DIR / "email_config.json"

# Log ayarları
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = "DEBUG"

# Yedekleme ayarları
MAX_BACKUPS = 5  # Maksimum yedek sayısı
BACKUP_INTERVAL = 24 * 60 * 60  # Yedekleme aralığı (saniye)

# E-posta ayarları
EMAIL_CONFIG = {
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "USE_TLS": True,
    "SUBJECT": "Tamir Atölyesi - Otomatik Yedekleme",
    "BODY": "Otomatik yedekleme dosyası ektedir.",
    "email": "",
    "password": ""
}

# Tema ayarları
THEME_NAME = "azure"
ICON_THEME = "default"

# Pencere ayarları
WINDOW_SIZE = {
    "width_ratio": 0.8,  # Ekran genişliğinin %80'i
    "height_ratio": 0.8  # Ekran yüksekliğinin %80'i
}

# Veritabanı ayarları
DB_CONFIG = {
    "backup_on_start": True,  # Başlangıçta yedek al
    "vacuum_on_close": True,  # Kapanışta veritabanını optimize et
    "foreign_keys": True      # Yabancı anahtar desteği
}

# Uygulama ayarları
APP_CONFIG = {
    "name": "Tamir Atölyesi Yönetim Sistemi",
    "version": "1.0.0",
    "company": "Mehmet Said ÖZSOY",
    "website": "https://github.com/mehmetsaidozsoy/tamir-atolyesi",
    "support_email": "support@tamiratolyesi.com"
}

# Dizinleri oluştur
for directory in [DATA_DIR, BACKUP_DIR, LOG_DIR, ICONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Veritabanı ayarları
DB_NAME = "tamir_atolyesi.db"
DB_PATH = DATA_DIR / DB_NAME

# Rapor ayarları
REPORT_DIR = Path.home() / "Documents" / "TamirAtolyesiRaporlari"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Yedekleme ayarları
BACKUP_CONFIG = {
    "auto_backup": True,
    "backup_interval": 24,  # saat
    "backup_dir": DATA_DIR / "backups",
    "max_backups": 7  # Maksimum yedek sayısı
}

# Tema ayarları
THEME_CONFIG = {
    "default_theme": "arc",
    "available_themes": ["arc", "clearlooks", "radiance"]
}

# Dil ayarları
LANGUAGE_CONFIG = {
    "default_language": "tr",
    "available_languages": ["tr", "en"]
}

# Uygulama ayarları
APP_NAME = "Tamir Atölyesi Yönetim Sistemi"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Yazılım Ekibi"
APP_EMAIL = "destek@otoservis.com"
APP_WEBSITE = "https://www.otoservis.com"

# Pencere ayarları
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# Tema ayarları
BACKGROUND_COLOR = '#f0f0f0'
FOREGROUND_COLOR = '#333333'
ACCENT_COLOR = '#007bff'
ERROR_COLOR = '#dc3545'
SUCCESS_COLOR = '#28a745'
WARNING_COLOR = '#ffc107'
INFO_COLOR = '#17a2b8'

# Tablo ayarları
TABLE_ROW_HEIGHT = 25
TABLE_FONT_SIZE = 10
TABLE_HEADER_BG = '#e9ecef'
TABLE_HEADER_FG = '#495057'
TABLE_ROW_BG = '#ffffff'
TABLE_ROW_ALT_BG = '#f8f9fa'
TABLE_SELECTED_BG = '#007bff'
TABLE_SELECTED_FG = '#ffffff'

# Form ayarları
FORM_PADDING = 10
FORM_LABEL_WIDTH = 150
FORM_ENTRY_WIDTH = 300
FORM_BUTTON_WIDTH = 100
FORM_BUTTON_HEIGHT = 30

# Tooltip ayarları
TOOLTIP_DELAY = 500  # milisaniye
TOOLTIP_BG = '#333333'
TOOLTIP_FG = '#ffffff'
TOOLTIP_FONT = ('Segoe UI', 9)

# Mesaj kutusu ayarları
MSG_BOX_WIDTH = 400
MSG_BOX_HEIGHT = 200
MSG_BOX_TIMEOUT = 3000  # milisaniye

# Onarım durumları
REPAIR_STATUSES = [
    'Beklemede',
    'Devam Ediyor',
    'Parça Bekliyor',
    'Tamamlandı',
    'İptal Edildi'
]

# İzin seviyeleri
PERMISSION_LEVELS = {
    'Ziyaretçi': 0,
    'Teknisyen': 1,
    'Yönetici': 2,
    'Admin': 3
}

# Varsayılan admin kullanıcısı
DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin123',
    'email': 'admin@otoservis.com',
    'permission_level': PERMISSION_LEVELS['Admin']
}

# E-posta ayarlarını yükle veya oluştur
def load_email_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                EMAIL_CONFIG.update(loaded_config)
        return EMAIL_CONFIG
    except Exception as e:
        logger.error(f"E-posta ayarları yüklenirken hata: {e}")
        return EMAIL_CONFIG

def save_email_config(config):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"E-posta ayarları kaydedilirken hata: {e}")
        return False

# E-posta ayarlarını yükle
EMAIL_CONFIG = load_email_config() 