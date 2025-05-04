import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

class LoginDialog:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.result = False
        
        # Dialog penceresini oluştur
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Giriş")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        
        # Pencereyi ortala
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')
        
        # Frame
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill="both", expand=True)
        
        # Kullanıcı adı
        ttk.Label(frame, text="Kullanıcı Adı:").grid(row=0, column=0, sticky="w", pady=5)
        self.username = ttk.Entry(frame)
        self.username.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Şifre
        ttk.Label(frame, text="Şifre:").grid(row=1, column=0, sticky="w", pady=5)
        self.password = ttk.Entry(frame, show="*")
        self.password.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Giriş butonu
        ttk.Button(frame, text="Giriş", command=self.do_login).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Enter tuşu ile giriş
        self.dialog.bind("<Return>", lambda e: self.do_login())
        
        # İlk alana odaklan
        self.username.focus()
        
        # Dialog'u modal yap
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Dialog kapandığında ana pencereyi tekrar göster
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Dialog'u bekle
        parent.wait_window(self.dialog)
        
    def do_login(self):
        """Giriş işlemini gerçekleştirir"""
        username = self.username.get().strip()
        password = self.password.get().strip()
        
        if not username or not password:
            messagebox.showerror("Hata", "Kullanıcı adı ve şifre zorunludur!")
            return
        
        # Kullanıcı doğrulama
        user = self.db.kullanici_dogrula(username, password)
        if user:
            logger.info(f"Kullanıcı girişi başarılı: {username}")
            self.result = True
            self.dialog.destroy()
        else:
            logger.warning(f"Geçersiz giriş denemesi: {username}")
            messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre!")
            self.password.delete(0, "end")
            self.password.focus()
            
    def on_close(self):
        """Dialog kapatıldığında çağrılır"""
        self.result = False
        self.dialog.destroy() 