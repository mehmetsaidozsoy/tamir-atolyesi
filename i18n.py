class I18n:
    def __init__(self):
        self.current_language = "tr"
        self.translations = {
            "tr": {
                "login": "Giriş",
                "username": "Kullanıcı Adı",
                "password": "Şifre",
                "login_error": "Geçersiz kullanıcı adı veya şifre!",
                "customers": "Müşteriler",
                "repairs": "Tamirler",
                "settings": "Ayarlar",
                "dashboard": "Gösterge Paneli",
                "save": "Kaydet",
                "delete": "Sil",
                "edit": "Düzenle",
                "search": "Ara",
                "report": "Rapor",
                "backup": "Yedekle",
                "test": "Test",
                "close": "Kapat"
            },
            "en": {
                "login": "Login",
                "username": "Username",
                "password": "Password",
                "login_error": "Invalid username or password!",
                "customers": "Customers",
                "repairs": "Repairs",
                "settings": "Settings",
                "dashboard": "Dashboard",
                "save": "Save",
                "delete": "Delete",
                "edit": "Edit",
                "search": "Search",
                "report": "Report",
                "backup": "Backup",
                "test": "Test",
                "close": "Close"
            }
        }
    
    def get(self, key):
        """Verilen anahtarın çevirisini döndürür"""
        return self.translations.get(self.current_language, {}).get(key, key)
    
    def set_language(self, language):
        """Dili değiştirir"""
        if language in self.translations:
            self.current_language = language 