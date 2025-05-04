import tkinter as tk
from tkinter import ttk, messagebox
from database import VeritabaniYonetici
from gui.tamir_atolyesi_gui import TamirAtolyesiGUI
import hashlib

class TamirAtolyesiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.db = VeritabaniYonetici()
        self.title("Tamir Atölyesi")
        
        # Ana container
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        
        # Aktif frame'i tutacak değişken
        self.current_frame = None
        
        # Login ekranını göster
        self.show_login()
        
    def show_login(self):
        # Mevcut frame varsa kaldır
        if self.current_frame:
            self.current_frame.destroy()
        
        # Login frame
        login_frame = tk.Frame(self.container, bg='#f0f0f0')
        login_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Pencere ayarları
        self.title("Giriş")
        self.geometry("300x200")
        self.resizable(False, False)
        
        # Form elemanları
        tk.Label(login_frame, text="Kullanıcı Adı:", bg='#f0f0f0', font=('Arial', 10)).pack(pady=5)
        self.username = tk.Entry(login_frame, font=('Arial', 10))
        self.username.pack(pady=5, fill='x')
        
        tk.Label(login_frame, text="Şifre:", bg='#f0f0f0', font=('Arial', 10)).pack(pady=5)
        self.password = tk.Entry(login_frame, show="*", font=('Arial', 10))
        self.password.pack(pady=5, fill='x')
        
        # Butonlar
        button_frame = tk.Frame(login_frame, bg='#f0f0f0')
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Giriş",
            command=self.login,
            width=10,
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="İptal",
            command=self.quit,
            width=10,
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Enter tuşu ile giriş
        self.bind('<Return>', lambda e: self.login())
        
        # Kullanıcı adı alanına odaklan
        self.username.focus()
        
        self.current_frame = login_frame
        
    def login(self):
        username = self.username.get()
        password = self.password.get()
        
        if not username or not password:
            messagebox.showwarning("Uyarı", "Kullanıcı adı ve şifre gereklidir!")
            return
        
        user = self.db.kullanici_dogrula(username, password)
        if user:
            self.show_main_app()
        else:
            messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre!")
            self.password.delete(0, tk.END)
    
    def show_main_app(self):
        # Mevcut frame'i kaldır
        if self.current_frame:
            self.current_frame.destroy()
        
        # Ana pencere ayarları
        self.title("Tamir Atölyesi Yönetim Sistemi")
        self.state('zoomed')
        self.resizable(True, True)
        
        # Ana uygulama frame'i
        main_frame = tk.Frame(self.container)
        main_frame.pack(expand=True, fill='both')
        
        try:
            # Ana uygulamayı başlat
            TamirAtolyesiGUI(main_frame)
            self.current_frame = main_frame
            
            # Çıkış butonu ekle
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Ana uygulama başlatılırken hata oluştu: {str(e)}")
            self.show_login()
    
    def on_closing(self):
        if messagebox.askokcancel("Çıkış", "Uygulamadan çıkmak istediğinize emin misiniz?"):
            self.quit()

if __name__ == "__main__":
    try:
        app = TamirAtolyesiApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Hata", str(e)) 