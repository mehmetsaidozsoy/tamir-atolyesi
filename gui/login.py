import tkinter as tk
from tkinter import ttk, messagebox
from database import VeritabaniYonetici

class LoginForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Pencere ayarları
        self.title("Giriş")
        self.geometry("300x150")
        self.resizable(False, False)
        
        # Pencereyi ortala
        self.center_window()
        
        # Modal pencere ayarları
        self.transient(parent)
        self.grab_set()
        
        # Değişkenler
        self.db = VeritabaniYonetici()
        self.login_successful = False
        self.username = None
        self.parent = parent
        
        # Form elemanları
        ttk.Label(self, text="Kullanıcı Adı:").pack(pady=5)
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack(pady=5)
        
        ttk.Label(self, text="Şifre:").pack(pady=5)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack(pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Giriş", command=self.giris_yap).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", command=self.iptal).pack(side=tk.LEFT, padx=5)
        
        # Enter tuşu ile giriş yapma
        self.bind('<Return>', lambda e: self.giris_yap())
        
        # Pencereyi ön plana getir
        self.lift()
        self.focus_force()
        
        # Kullanıcı adı alanına odaklan
        self.username_entry.focus()
        
        # Pencere kapatma düğmesi kontrolü
        self.protocol("WM_DELETE_WINDOW", self.iptal)
        
        # Pencereyi merkeze al
        self.center_window()
        
    def center_window(self):
        """Pencereyi ekranın ortasına konumlandırır"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
    def giris_yap(self):
        kullanici_adi = self.username_entry.get()
        sifre = self.password_entry.get()
        
        if not kullanici_adi or not sifre:
            messagebox.showwarning("Uyarı", "Kullanıcı adı ve şifre gereklidir")
            return
            
        sonuc = self.db.kullanici_dogrula(kullanici_adi, sifre)
        if sonuc:
            self.login_successful = True
            self.username = kullanici_adi
            self.after(100, self.destroy)  # Pencereyi biraz bekleyip kapat
        else:
            messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre!")
            self.password_entry.delete(0, tk.END)
            
    def iptal(self):
        """Uygulamadan çık"""
        self.login_successful = False
        self.after(100, self.destroy)  # Pencereyi biraz bekleyip kapat 