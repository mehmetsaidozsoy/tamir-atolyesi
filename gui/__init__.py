"""
GUI paketi için başlatma dosyası.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .backup_manager import BackupManager
from database import VeritabaniYonetici

class TamirAtolyesiGUI:
    def __init__(self, root, username):
        self.root = root
        self.db = VeritabaniYonetici()
        self.current_user = username
        
        # Ana pencere ayarları
        self.root.title("Tamir Atölyesi Yönetim Sistemi")
        self.root.geometry("1000x600")
        
        # Ana frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Üst bilgi çerçevesi
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Hoş geldiniz mesajı
        ttk.Label(
            self.header_frame, 
            text=f"Hoş geldiniz, {self.current_user}",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT, pady=5)
        
        # Menü oluştur
        self.menu_olustur()
        
        # Dashboard frame
        self.dashboard_frame = ttk.LabelFrame(self.main_frame, text="Genel Durum")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sol panel - İstatistikler
        self.stats_frame = ttk.Frame(self.dashboard_frame)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sağ panel - Aktif tamirler
        self.active_frame = ttk.Frame(self.dashboard_frame)
        self.active_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # İstatistikleri göster
        self.istatistikleri_goster()
        
        # Aktif tamirleri göster
        self.aktif_tamirleri_goster()
        
        # Otomatik yenileme
        self.root.after(60000, self.dashboard_guncelle)
        
    def menu_olustur(self):
        """Ana menüyü oluşturur"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Araç menüsü
        arac_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Araçlar", menu=arac_menu)
        arac_menu.add_command(label="Araç Girişi", command=self.arac_girisi_ac)
        
        # Tamir menüsü
        tamir_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tamir", menu=tamir_menu)
        tamir_menu.add_command(label="Tamir İşlemleri", command=self.tamir_islemleri_ac)
        
        # Yönetim menüsü
        yonetim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yönetim", menu=yonetim_menu)
        yonetim_menu.add_command(label="Yedekleme", command=self.yedekleme_ac)
        yonetim_menu.add_separator()
        yonetim_menu.add_command(label="Çıkış", command=self.cikis)
        
    def istatistikleri_goster(self):
        """İstatistikleri gösterir"""
        # İstatistik başlığı
        ttk.Label(
            self.stats_frame,
            text="Sistem İstatistikleri",
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Araç sayısı
        araclar = self.db.tum_araclar()
        ttk.Label(
            self.stats_frame,
            text=f"Toplam Araç Sayısı: {len(araclar)}",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=2)
        
        # Aktif tamir sayısı
        aktif_tamirler = self.db.aktif_onarimlar()
        ttk.Label(
            self.stats_frame,
            text=f"Aktif Tamir Sayısı: {len(aktif_tamirler)}",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=2)
        
        # Tamamlanan tamir sayısı
        tamamlanan = self.db.tamamlanan_onarimlar()
        ttk.Label(
            self.stats_frame,
            text=f"Tamamlanan Tamir Sayısı: {len(tamamlanan)}",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=2)
        
    def aktif_tamirleri_goster(self):
        """Aktif tamirleri listeler"""
        # Başlık
        ttk.Label(
            self.active_frame,
            text="Aktif Tamirler",
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Tamir listesi
        columns = ("Plaka", "Sorun", "Durum")
        self.aktif_liste = ttk.Treeview(
            self.active_frame,
            columns=columns,
            show="headings",
            height=10
        )
        
        # Başlıkları ayarla
        self.aktif_liste.heading("Plaka", text="Plaka")
        self.aktif_liste.heading("Sorun", text="Sorun")
        self.aktif_liste.heading("Durum", text="Durum")
        
        # Sütun genişliklerini ayarla
        self.aktif_liste.column("Plaka", width=100)
        self.aktif_liste.column("Sorun", width=200)
        self.aktif_liste.column("Durum", width=100)
        
        self.aktif_liste.pack(fill=tk.BOTH, expand=True)
        
        # Aktif tamirleri listele
        self.aktif_tamirleri_guncelle()
        
    def aktif_tamirleri_guncelle(self):
        """Aktif tamir listesini günceller"""
        # Mevcut listeyi temizle
        for item in self.aktif_liste.get_children():
            self.aktif_liste.delete(item)
            
        # Aktif tamirleri al ve listele
        aktif_tamirler = self.db.aktif_onarimlar()
        for tamir in aktif_tamirler:
            self.aktif_liste.insert("", tk.END, values=(
                tamir[11],  # plaka
                tamir[4][:30] + "..." if len(tamir[4]) > 30 else tamir[4],  # sorun
                tamir[8]  # durum
            ))
            
    def dashboard_guncelle(self):
        """Dashboard'ı günceller"""
        self.istatistikleri_goster()
        self.aktif_tamirleri_guncelle()
        # Bir dakika sonra tekrar güncelle
        self.root.after(60000, self.dashboard_guncelle)
        
    def arac_girisi_ac(self):
        """Araç girişi penceresini açar"""
        # AracGiris(self.root)
        
    def tamir_islemleri_ac(self):
        """Tamir işlemleri penceresini açar"""
        # TamirIslemleri(self.root)
        
    def yedekleme_ac(self):
        """Yedekleme penceresini açar"""
        BackupManager(self.root)
        
    def cikis(self):
        """Uygulamadan çıkış yapar"""
        if messagebox.askyesno("Çıkış", "Uygulamadan çıkmak istediğinizden emin misiniz?"):
            self.root.quit() 