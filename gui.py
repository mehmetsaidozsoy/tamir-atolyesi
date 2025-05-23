import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
from models import Musteri, Tamir, MaliyetTahmini
from database import VeritabaniYonetici
from fpdf import FPDF
from tkcalendar import DateEntry
import pandas as pd
import os
from pathlib import Path
import logging
from backup_manager import YedekYoneticisi
from config import EMAIL_CONFIG
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from cryptography.fernet import Fernet
from i18n import I18n
from tqdm import tqdm
import threading
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys

logger = logging.getLogger(__name__)

class TamirAtolyesiGUI:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Ana pencereyi başlangıçta gizle
        
        # Giriş başarılı olana kadar ana pencereyi gösterme
        if not self.kullanici_girisi():
            self.root.quit()
            return
            
        self.root.deiconify()  # Ana pencereyi göster
        self.root.title("Tamir Atölyesi Yönetim Sistemi")
        self.root.state('zoomed')  # Tam ekran yap
        
        # Pencereyi ekranın ortasına konumlandır
        self.center_window()
        
        logger.info("TamirAtolyesiGUI başlatılıyor...")
        
        # Çoklu dil desteği
        self.i18n = I18n()
        self.current_language = "tr"
        
        # Şifreleme anahtarı
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Klavye kısayolları
        self.root.bind('<Control-s>', lambda e: self.musteri_kaydet())
        self.root.bind('<Control-n>', lambda e: self.yeni_musteri())
        self.root.bind('<Control-f>', lambda e: self.musteri_ara())
        self.root.bind('<Control-p>', lambda e: self.rapor_goster())
        self.root.bind('<F5>', lambda e: self.musteri_listesini_guncelle())
        
        # Stil tanımlamaları
        logger.debug("Stil tanımlamaları yapılıyor...")
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#2196F3")
        self.style.configure("TLabel", padding=5, font=("Segoe UI", 10))
        self.style.configure("TEntry", padding=5, font=("Segoe UI", 10))
        self.style.configure("Treeview", rowheight=25, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        
        # Renk paleti
        self.colors = {
            "primary": "#2196F3",
            "secondary": "#FFC107",
            "success": "#4CAF50",
            "danger": "#F44336",
            "warning": "#FF9800",
            "info": "#00BCD4",
            "light": "#F5F5F5",
            "dark": "#212121"
        }
        
        # İkonlar
        logger.debug("İkonlar yükleniyor...")
        self.icons = {
            "save": self.load_icon("save.png"),
            "delete": self.load_icon("delete.png"),
            "edit": self.load_icon("edit.png"),
            "search": self.load_icon("search.png"),
            "report": self.load_icon("report.png"),
            "settings": self.load_icon("settings.png"),
            "backup": self.load_icon("backup.png"),
            "user": self.load_icon("user.png"),
            "test": self.load_icon("test.png")
        }
        
        # Ana pencere için grid yapılandırması
        self.root.grid_rowconfigure(0, weight=1)
        logger.info("Kullanıcı girişi başlatılıyor...")
        # Ana pencereyi gizle ve kullanıcı girişini göster
        self.root.withdraw()
        if not self.kullanici_girisi():
            logger.warning("Kullanıcı girişi başarısız, uygulama kapatılıyor...")
            self.root.destroy()
            return
            
        logger.info("Kullanıcı girişi başarılı, ana pencere hazırlanıyor...")
        # Ana pencereyi göster
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        self.root.update()
        
        # Menü çubuğu oluştur
        self.menu_olustur()
        
        # Ana pencere için grid yapılandırması
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Diğer bileşenleri başlat
        self.init_components()
        
    def init_components(self):
        """Diğer bileşenleri başlatır"""
        logger.debug("Veritabanı bağlantısı kuruluyor...")
        # Veritabanı bağlantısı
        self.db = VeritabaniYonetici()
        self.conn = self.db.conn
        self.cursor = self.db.cursor
        
        logger.debug("Yedekleme yöneticisi başlatılıyor...")
        # Yedekleme yöneticisi
        self.yedek_yoneticisi = YedekYoneticisi()
        
        logger.debug("Notebook ve sekmeler oluşturuluyor...")
        # Notebook (Sekmeler) oluştur
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Sekmeleri oluştur
        self.create_tabs()
        
        # Klavye kısayolları
        self.klavye_kisayollari_ekle()
        
        # Otomatik yedeklemeyi başlat
        self.yedek_yoneticisi.start_scheduler()
        
        # Aktivite loglarını başlat
        self.aktivite_log_baslat()
        
        # Program kapatıldığında tüm kaynakları temizle
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_tabs(self):
        """Sekmeleri oluşturur"""
        logger.debug("Sekmeler oluşturuluyor...")
        
        # Müşteri sekmesi
        self.musteri_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.musteri_frame, text="Müşteriler")
        
        # Tamir sekmesi
        self.tamir_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tamir_frame, text="Tamirler")
        
        # Ayarlar sekmesi
        self.ayarlar_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.ayarlar_frame, text="Ayarlar")
        
        # Dashboard sekmesi
        self.dashboard_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        # Sekme içeriklerini oluştur
        self.musteri_sekmesi_olustur()
        self.tamir_sekmesi_olustur()
        self.ayarlar_sekmesi_olustur()
        self.dashboard_sekmesi_olustur()
        
    def kullanici_girisi(self):
        """Kullanıcı girişi kontrolü yapar"""
        try:
            logger.debug("Kullanıcı giriş penceresi açılıyor...")
            
            # Giriş penceresini oluştur
            login = tk.Toplevel(self.root)
            login.title("Giriş")
            login.geometry("300x150")
            login.resizable(False, False)
            login.transient(self.root)  # Ana pencereye bağlı modal pencere
            login.grab_set()  # Pencereyi modal yap
            
            # Pencereyi ortala
            login.update_idletasks()
            width = login.winfo_width()
            height = login.winfo_height()
            x = (login.winfo_screenwidth() // 2) - (width // 2)
            y = (login.winfo_screenheight() // 2) - (height // 2)
            login.geometry(f'+{x}+{y}')
            
            # Frame
            frame = ttk.Frame(login, padding="20")
            frame.pack(fill="both", expand=True)
            
            # Kullanıcı adı ve şifre alanları
            ttk.Label(frame, text="Kullanıcı Adı:").grid(row=0, column=0, sticky="w")
            username = ttk.Entry(frame)
            username.grid(row=0, column=1, padx=5, pady=5)
            username.focus()
            
            ttk.Label(frame, text="Şifre:").grid(row=1, column=0, sticky="w")
            password = ttk.Entry(frame, show="*")
            password.grid(row=1, column=1, padx=5, pady=5)
            
            # Giriş sonucu
            self.login_success = False
            
            def do_login():
                # Burada gerçek kullanıcı doğrulama yapılacak
                if username.get() == "admin" and password.get() == "1234":
                    self.login_success = True
                    login.destroy()
                else:
                    messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre!")
                    
            # Giriş butonu
            login_btn = ttk.Button(frame, text="Giriş", command=do_login)
            login_btn.grid(row=2, column=0, columnspan=2, pady=10)
            
            # Enter tuşu ile giriş
            login.bind('<Return>', lambda e: do_login())
            
            # Pencereyi modal yap
            login.focus_force()
            self.root.wait_window(login)
            
            return self.login_success
            
        except Exception as e:
            logger.error(f"Giriş hatası: {str(e)}")
            messagebox.showerror("Hata", "Giriş işlemi sırasında bir hata oluştu!")
            return False
    
    def on_closing(self):
        """Program kapatıldığında tüm kaynakları temizler"""
        try:
            if hasattr(self, 'yedek_yoneticisi'):
                self.yedek_yoneticisi.stop_scheduler()
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
            self.root.destroy()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Program kapatılırken hata: {str(e)}")
            sys.exit(1)
    
    def load_icon(self, icon_name):
        """İkon dosyasını yükler"""
        try:
            icon_path = Path("icons") / icon_name
            if not icon_path.exists():
                logger.warning(f"İkon dosyası bulunamadı: {icon_path}")
                return None
            return ImageTk.PhotoImage(Image.open(icon_path))
        except Exception as e:
            logger.error(f"İkon yüklenirken hata: {str(e)}")
            return None
            
    def klavye_kisayollari_ekle(self):
        """Klavye kısayollarını ekler"""
        # Kısayollar zaten __init__ içinde tanımlandı
        pass
        
    def aktivite_log_baslat(self):
        self.aktivite_log = []
        self.log_file = "activity_log.json"
        
    def aktivite_kaydet(self, action, details):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": self.current_user,
            "action": action,
            "details": details
        }
        self.aktivite_log.append(log_entry)
        
        # Log dosyasına kaydet
        with open(self.log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
            
    def dashboard_sekmesi_olustur(self):
        # İstatistik kartları
        stats_frame = ttk.Frame(self.dashboard_frame)
        stats_frame.pack(fill="x", pady=10)
        
        # Aylık gelir kartı
        income_card = ttk.LabelFrame(stats_frame, text="Aylık Gelir")
        income_card.pack(side="left", padx=10, fill="both", expand=True)
        self.income_label = ttk.Label(income_card, text="0 TL", font=("Segoe UI", 24, "bold"))
        self.income_label.pack(pady=20)
        
        # Aktif tamirler kartı
        active_card = ttk.LabelFrame(stats_frame, text="Aktif Tamirler")
        active_card.pack(side="left", padx=10, fill="both", expand=True)
        self.active_label = ttk.Label(active_card, text="0", font=("Segoe UI", 24, "bold"))
        self.active_label.pack(pady=20)
        
        # Müşteri sayısı kartı
        customer_card = ttk.LabelFrame(stats_frame, text="Toplam Müşteri")
        customer_card.pack(side="left", padx=10, fill="both", expand=True)
        self.customer_label = ttk.Label(customer_card, text="0", font=("Segoe UI", 24, "bold"))
        self.customer_label.pack(pady=20)
        
        # Grafikler
        charts_frame = ttk.Frame(self.dashboard_frame)
        charts_frame.pack(fill="both", expand=True, pady=10)
        
        # Gelir grafiği
        income_chart = ttk.LabelFrame(charts_frame, text="Aylık Gelir Trendi")
        income_chart.pack(side="left", padx=10, fill="both", expand=True)
        self.income_fig = plt.Figure(figsize=(6, 4))
        self.income_ax = self.income_fig.add_subplot(111)
        self.income_canvas = FigureCanvasTkAgg(self.income_fig, master=income_chart)
        self.income_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Tamir durumu grafiği
        status_chart = ttk.LabelFrame(charts_frame, text="Tamir Durumları")
        status_chart.pack(side="left", padx=10, fill="both", expand=True)
        self.status_fig = plt.Figure(figsize=(6, 4))
        self.status_ax = self.status_fig.add_subplot(111)
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, master=status_chart)
        self.status_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Dashboard'u güncelle
        self.dashboard_guncelle()
        
    def dashboard_guncelle(self):
        # İstatistikleri güncelle
        self.income_label.config(text=f"{self.get_monthly_income():.2f} TL")
        self.active_label.config(text=str(self.get_active_repairs()))
        self.customer_label.config(text=str(self.get_total_customers()))
        
        # Gelir grafiğini güncelle
        self.update_income_chart()
        
        # Durum grafiğini güncelle
        self.update_status_chart()
        
    def get_monthly_income(self):
        try:
            self.cursor.execute('''
                SELECT SUM(maliyet) FROM tamirler 
                WHERE strftime('%Y-%m', tarih) = strftime('%Y-%m', 'now')
                AND durum = 'Tamamlandı'
            ''')
            return self.cursor.fetchone()[0] or 0
        except:
            return 0
            
    def get_active_repairs(self):
        try:
            self.cursor.execute('''
                SELECT COUNT(*) FROM tamirler 
                WHERE durum IN ('Açık', 'Devam Ediyor')
            ''')
            return self.cursor.fetchone()[0]
        except:
            return 0
            
    def get_total_customers(self):
        try:
            self.cursor.execute('SELECT COUNT(*) FROM musteriler')
            return self.cursor.fetchone()[0]
        except:
            return 0
            
    def update_income_chart(self):
        try:
            self.cursor.execute('''
                SELECT strftime('%Y-%m', tarih) as ay, SUM(maliyet) as toplam
                FROM tamirler 
                WHERE durum = 'Tamamlandı'
                GROUP BY ay
                ORDER BY ay DESC
                LIMIT 12
            ''')
            data = self.cursor.fetchall()
            
            self.income_ax.clear()
            if data:
                months = [row[0] for row in data]
                amounts = [row[1] for row in data]
                sns.barplot(x=months, y=amounts, ax=self.income_ax)
                self.income_ax.set_title('Aylık Gelir Trendi')
                self.income_ax.set_xlabel('Ay')
                self.income_ax.set_ylabel('Gelir (TL)')
            self.income_canvas.draw()
        except Exception as e:
            logger.error(f"Gelir grafiği güncellenirken hata: {str(e)}")
            
    def update_status_chart(self):
        try:
            self.cursor.execute('''
                SELECT durum, COUNT(*) as sayi
                FROM tamirler
                GROUP BY durum
            ''')
            data = self.cursor.fetchall()
            
            self.status_ax.clear()
            if data:
                statuses = [row[0] for row in data]
                counts = [row[1] for row in data]
                sns.barplot(x=statuses, y=counts, ax=self.status_ax)
                self.status_ax.set_title('Tamir Durumları')
                self.status_ax.set_xlabel('Durum')
                self.status_ax.set_ylabel('Sayı')
            self.status_canvas.draw()
        except Exception as e:
            logger.error(f"Durum grafiği güncellenirken hata: {str(e)}")
            
    def show_loading(self, message):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Yükleniyor")
        self.loading_window.geometry("300x100")
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()
        
        ttk.Label(self.loading_window, text=message).pack(pady=10)
        self.progress = ttk.Progressbar(self.loading_window, mode='indeterminate')
        self.progress.pack(fill="x", padx=10, pady=10)
        self.progress.start()
        
    def hide_loading(self):
        if hasattr(self, 'loading_window'):
            self.progress.stop()
            self.loading_window.destroy()
            
    def show_tooltip(self, widget, text):
        """Tooltip'i gösterir"""
        def show(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # Eğer zaten bir tooltip varsa yok et
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            # Tooltip penceresini en üstte tut
            self.tooltip.attributes('-topmost', True)
            
            label = ttk.Label(self.tooltip, text=text, justify='left',
                            background="#ffffe0", relief='solid', borderwidth=1,
                            padding=5)
            label.pack()
            
            # Tooltip'i 3 saniye sonra otomatik kapat
            self.root.after(3000, hide)
            
        def hide(event=None):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind('<Enter>', show)
        widget.bind('<Leave>', hide)
        
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side="top", fill="x")
        
        buttons = [
            ("Yeni Müşteri", self.icons["user"], self.yeni_musteri),
            ("Yeni Tamir", self.icons["edit"], self.yeni_tamir),
            ("Rapor", self.icons["report"], self.rapor_goster),
            ("Yedekle", self.icons["backup"], self.manuel_yedek_al),
            ("Ayarlar", self.icons["settings"], self.ayarlar_sekmesi_olustur)
        ]
        
        for text, icon, command in buttons:
            btn = ttk.Button(toolbar, text=text, image=icon, compound="left", command=command)
            btn.pack(side="left", padx=5, pady=5)
            self.show_tooltip(btn, text)
            
    def create_statusbar(self):
        self.statusbar = ttk.Label(self.root, text="Hazır", relief="sunken", anchor="w")
        self.statusbar.pack(side="bottom", fill="x")
        
    def update_status(self, message):
        self.statusbar.config(text=message)
        
    def show_notification(self, title, message, type="info"):
        colors = {
            "info": self.colors["info"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "error": self.colors["danger"]
        }
        
        notification = tk.Toplevel(self.root)
        notification.title(title)
        notification.geometry("300x100")
        notification.attributes('-topmost', True)
        
        frame = ttk.Frame(notification)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text=message, wraplength=280).pack(pady=10)
        ttk.Button(frame, text="Tamam", command=notification.destroy).pack()
        
        # 3 saniye sonra otomatik kapan
        self.root.after(3000, notification.destroy)
    
    def __del__(self):
        """Program kapatılırken zamanlayıcıyı durdur"""
        if hasattr(self, 'yedek_yoneticisi'):
            self.yedek_yoneticisi.stop_scheduler()
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        
    def menu_olustur(self):
        """Menü çubuğunu oluşturur"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Dosya menüsü
        dosya_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=dosya_menu)
        dosya_menu.add_command(label="Yedekle", command=self.manuel_yedek_al)
        dosya_menu.add_separator()
        dosya_menu.add_command(label="Çıkış", command=self.root.quit)
        
        # Ayarlar menüsü
        ayarlar_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayarlar", menu=ayarlar_menu)
        ayarlar_menu.add_command(label="E-posta Ayarları", command=self.email_ayarlari_goster)
        ayarlar_menu.add_command(label="Kullanıcı Ayarları", command=self.kullanici_ayarlari_goster)
        
        # Yardım menüsü
        yardim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=yardim_menu)
        yardim_menu.add_command(label="Hakkında", command=self.hakkinda_goster)
    
    def manuel_yedek_al(self):
        """Manuel yedekleme işlemini gerçekleştirir"""
        try:
            self.show_loading("Yedekleme yapılıyor...")
            
            # Yedekleme yöneticisini başlat
            yedek_yoneticisi = YedekYoneticisi()
            
            # E-posta ayarlarını al
            self.cursor.execute("SELECT email, sifre FROM ayarlar WHERE id=1")
            ayarlar = self.cursor.fetchone()
            
            if ayarlar and ayarlar[0] and ayarlar[1]:
                # E-posta ayarlarını güncelle
                yedek_yoneticisi.email_ayarlarini_guncelle(
                    ayarlar[0],
                    ayarlar[1],
                    ayarlar[0],  # Kendine gönder
                    "manuel"  # Manuel yedekleme
                )
                
                # Yedekleme işlemini başlat
                if yedek_yoneticisi.manuel_yedek_al():
                    self.show_notification("Başarılı", "Yedekleme başarıyla tamamlandı", "success")
                    self.aktivite_kaydet("Yedekleme", "Manuel yedekleme yapıldı")
                else:
                    self.show_notification("Hata", "Yedekleme sırasında bir hata oluştu", "error")
            else:
                self.show_notification("Uyarı", "E-posta ayarları bulunamadı", "warning")
                
        except Exception as e:
            logger.error(f"Manuel yedekleme hatası: {str(e)}")
            self.show_notification("Hata", "Yedekleme sırasında bir hata oluştu", "error")
        finally:
            self.hide_loading()
    
    def kullanici_ayarlari_goster(self):
        """Kullanıcı ayarları penceresini gösterir"""
        KullaniciAyarlariDialog(self.root)
    
    def hakkinda_goster(self):
        """Hakkında penceresini gösterir"""
        messagebox.showinfo(
            "Hakkında",
            "Tamir Atölyesi Yönetim Sistemi\n\n"
            "Sürüm: 1.0.0\n"
            "© 2025 Tüm hakları saklıdır.\n\n"
            "Bu program tamir atölyelerinin müşteri ve tamir kayıtlarını\n"
            "yönetmek için Mehmet Said ÖZSOY tarafından tasarlanmıştır."
        )
    
    def musteri_sekmesi_olustur(self):
        # Sol panel - Müşteri bilgileri formu
        left_panel = ttk.LabelFrame(self.musteri_frame, text="Müşteri Bilgileri", padding="20")
        left_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Form alanları
        form_frame = ttk.Frame(left_panel)
        form_frame.pack(fill="both", expand=True)
        
        # Müşteri adı
        ttk.Label(form_frame, text="Müşteri Adı:").grid(row=0, column=0, sticky="w", pady=5)
        self.musteri_adi = ttk.Entry(form_frame, width=30)
        self.musteri_adi.grid(row=0, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.musteri_adi, "Müşterinin tam adını giriniz")
        self.musteri_adi.bind('<FocusIn>', lambda e: self.musteri_adi.configure(background='white'))
        self.musteri_adi.bind('<FocusOut>', lambda e: self.musteri_adi.configure(background='#f0f0f0'))
        
        # Telefon
        ttk.Label(form_frame, text="Telefon:").grid(row=1, column=0, sticky="w", pady=5)
        self.musteri_telefon = ttk.Entry(form_frame, width=30)
        self.musteri_telefon.grid(row=1, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.musteri_telefon, "Müşterinin telefon numarasını giriniz")
        self.musteri_telefon.bind('<FocusIn>', lambda e: self.musteri_telefon.configure(background='white'))
        self.musteri_telefon.bind('<FocusOut>', lambda e: self.musteri_telefon.configure(background='#f0f0f0'))
        
        # E-posta
        ttk.Label(form_frame, text="E-posta:").grid(row=2, column=0, sticky="w", pady=5)
        self.musteri_email = ttk.Entry(form_frame, width=30)
        self.musteri_email.grid(row=2, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.musteri_email, "Müşterinin e-posta adresini giriniz")
        self.musteri_email.bind('<FocusIn>', lambda e: self.musteri_email.configure(background='white'))
        self.musteri_email.bind('<FocusOut>', lambda e: self.musteri_email.configure(background='#f0f0f0'))
        
        # Adres
        ttk.Label(form_frame, text="Adres:").grid(row=3, column=0, sticky="w", pady=5)
        self.musteri_adres = tk.Text(form_frame, width=30, height=4)
        self.musteri_adres.grid(row=3, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.musteri_adres, "Müşterinin adresini giriniz")
        self.musteri_adres.bind('<FocusIn>', lambda e: self.musteri_adres.configure(background='white'))
        self.musteri_adres.bind('<FocusOut>', lambda e: self.musteri_adres.configure(background='#f0f0f0'))
        
        # Butonlar
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill="x", pady=10)
        
        self.musteri_kaydet_btn = ttk.Button(button_frame, text="Kaydet", 
                                           image=self.icons["save"], compound="left",
                                           command=self.musteri_kaydet)
        self.musteri_kaydet_btn.pack(side="left", padx=5)
        self.show_tooltip(self.musteri_kaydet_btn, "Müşteri bilgilerini kaydet")
        
        self.musteri_temizle_btn = ttk.Button(button_frame, text="Temizle",
                                            image=self.icons["delete"], compound="left",
                                            command=self.musteri_temizle)
        self.musteri_temizle_btn.pack(side="left", padx=5)
        self.show_tooltip(self.musteri_temizle_btn, "Formu temizle")
        
        # Sağ panel - Müşteri listesi
        right_panel = ttk.LabelFrame(self.musteri_frame, text="Müşteri Listesi", padding="20")
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Arama çubuğu
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill="x", pady=5)
        
        ttk.Label(search_frame, text="Ara:").pack(side="left", padx=5)
        self.musteri_arama = ttk.Entry(search_frame)
        self.musteri_arama.pack(side="left", fill="x", expand=True, padx=5)
        self.musteri_arama.bind('<KeyRelease>', self.musteri_arama_yap)
        self.show_tooltip(self.musteri_arama, "Müşteri adı veya telefon ile arama yapın")
        
        # Müşteri listesi
        columns = ("id", "ad", "telefon", "email", "adres")
        self.musteri_tree = ttk.Treeview(right_panel, columns=columns, show="headings")
        
        # Sütun başlıkları
        self.musteri_tree.heading("id", text="ID")
        self.musteri_tree.heading("ad", text="Müşteri Adı")
        self.musteri_tree.heading("telefon", text="Telefon")
        self.musteri_tree.heading("email", text="E-posta")
        self.musteri_tree.heading("adres", text="Adres")
        
        # Sütun genişlikleri
        self.musteri_tree.column("id", width=50)
        self.musteri_tree.column("ad", width=150)
        self.musteri_tree.column("telefon", width=100)
        self.musteri_tree.column("email", width=150)
        self.musteri_tree.column("adres", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.musteri_tree.yview)
        self.musteri_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid yapılandırması
        self.musteri_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Çift tıklama olayı
        self.musteri_tree.bind("<Double-1>", self.musteri_sec)
        
        # Müşteri listesini güncelle
        self.musteri_liste_guncelle()
        
    def musteri_arama_yap(self, event):
        search_term = self.musteri_arama.get().lower()
        for item in self.musteri_tree.get_children():
            values = self.musteri_tree.item(item)['values']
            if (search_term in values[1].lower() or  # Müşteri adı
                search_term in values[2].lower()):   # Telefon
                self.musteri_tree.selection_set(item)
                self.musteri_tree.see(item)
            else:
                self.musteri_tree.selection_remove(item)
                
    def musteri_liste_guncelle(self):
        # Mevcut öğeleri temizle
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)
            
        try:
            self.cursor.execute("SELECT * FROM musteriler ORDER BY ad")
            for row in self.cursor.fetchall():
                self.musteri_tree.insert("", "end", values=row)
        except Exception as e:
            logger.error(f"Müşteri listesi güncellenirken hata: {str(e)}")
            self.show_notification("Hata", "Müşteri listesi güncellenemedi", "error")
            
    def musteri_sec(self, event):
        selected_item = self.musteri_tree.selection()
        if selected_item:
            values = self.musteri_tree.item(selected_item)['values']
            self.musteri_adi.delete(0, tk.END)
            self.musteri_adi.insert(0, values[1])
            self.musteri_telefon.delete(0, tk.END)
            self.musteri_telefon.insert(0, values[2])
            self.musteri_email.delete(0, tk.END)
            self.musteri_email.insert(0, values[3])
            self.musteri_adres.delete("1.0", tk.END)
            self.musteri_adres.insert("1.0", values[4])
            
    def musteri_kaydet(self):
        try:
            ad = self.musteri_adi.get().strip()
            telefon = self.musteri_telefon.get().strip()
            email = self.musteri_email.get().strip()
            adres = self.musteri_adres.get("1.0", tk.END).strip()
            
            if not ad:
                self.show_notification("Uyarı", "Müşteri adı boş bırakılamaz", "warning")
                return
                
            selected_item = self.musteri_tree.selection()
            if selected_item:
                # Güncelleme
                musteri_id = self.musteri_tree.item(selected_item)['values'][0]
                self.cursor.execute("""
                    UPDATE musteriler 
                    SET ad=?, telefon=?, email=?, adres=?
                    WHERE id=?
                """, (ad, telefon, email, adres, musteri_id))
            else:
                # Yeni kayıt
                self.cursor.execute("""
                    INSERT INTO musteriler (ad, telefon, email, adres)
                    VALUES (?, ?, ?, ?)
                """, (ad, telefon, email, adres))
                
            self.conn.commit()
            self.musteri_liste_guncelle()
            self.musteri_temizle()
            self.show_notification("Başarılı", "Müşteri bilgileri kaydedildi", "success")
            self.aktivite_kaydet("Müşteri Kaydı", f"Müşteri: {ad}")
        except Exception as e:
            logger.error(f"Müşteri kaydedilirken hata: {str(e)}")
            self.show_notification("Hata", "Müşteri kaydedilemedi", "error")
            
    def musteri_temizle(self):
        self.musteri_adi.delete(0, tk.END)
        self.musteri_telefon.delete(0, tk.END)
        self.musteri_email.delete(0, tk.END)
        self.musteri_adres.delete("1.0", tk.END)
        self.musteri_tree.selection_remove(self.musteri_tree.selection())
    
    def tamir_sekmesi_olustur(self):
        # Sol panel - Tamir bilgileri formu
        left_panel = ttk.LabelFrame(self.tamir_frame, text="Tamir Bilgileri", padding="20")
        left_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Form alanları
        form_frame = ttk.Frame(left_panel)
        form_frame.pack(fill="both", expand=True)
        
        # Müşteri seçimi
        ttk.Label(form_frame, text="Müşteri:").grid(row=0, column=0, sticky="w", pady=5)
        self.tamir_musteri = ttk.Combobox(form_frame, width=30, state="readonly")
        self.tamir_musteri.grid(row=0, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.tamir_musteri, "Müşteri seçiniz")
        
        # Cihaz bilgisi
        ttk.Label(form_frame, text="Cihaz:").grid(row=1, column=0, sticky="w", pady=5)
        self.tamir_cihaz = ttk.Entry(form_frame, width=30)
        self.tamir_cihaz.grid(row=1, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.tamir_cihaz, "Tamir edilecek cihazı giriniz")
        
        # Sorun açıklaması
        ttk.Label(form_frame, text="Sorun:").grid(row=2, column=0, sticky="w", pady=5)
        self.tamir_sorun = tk.Text(form_frame, width=30, height=4)
        self.tamir_sorun.grid(row=2, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.tamir_sorun, "Cihazın sorununu detaylı açıklayınız")
        
        # Maliyet
        ttk.Label(form_frame, text="Maliyet:").grid(row=3, column=0, sticky="w", pady=5)
        self.tamir_maliyet = ttk.Entry(form_frame, width=30)
        self.tamir_maliyet.grid(row=3, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.tamir_maliyet, "Tahmini maliyeti giriniz")
        
        # Durum
        ttk.Label(form_frame, text="Durum:").grid(row=4, column=0, sticky="w", pady=5)
        self.tamir_durum = ttk.Combobox(form_frame, width=30, 
                                      values=["Açık", "Devam Ediyor", "Tamamlandı", "İptal"], 
                                      state="readonly")
        self.tamir_durum.grid(row=4, column=1, sticky="ew", pady=5)
        self.tamir_durum.set("Açık")
        
        # Butonlar
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill="x", pady=10)
        
        self.tamir_kaydet_btn = ttk.Button(button_frame, text="Kaydet", 
                                         image=self.icons["save"], compound="left",
                                         command=self.tamir_kaydet)
        self.tamir_kaydet_btn.pack(side="left", padx=5)
        self.show_tooltip(self.tamir_kaydet_btn, "Tamir bilgilerini kaydet")
        
        self.tamir_temizle_btn = ttk.Button(button_frame, text="Temizle",
                                          image=self.icons["delete"], compound="left",
                                          command=self.tamir_form_temizle)
        self.tamir_temizle_btn.pack(side="left", padx=5)
        self.show_tooltip(self.tamir_temizle_btn, "Formu temizle")
        
        # Sağ panel - Tamir listesi
        right_panel = ttk.LabelFrame(self.tamir_frame, text="Tamir Listesi", padding="20")
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Arama çubuğu
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill="x", pady=5)
        
        ttk.Label(search_frame, text="Ara:").pack(side="left", padx=5)
        self.tamir_arama = ttk.Entry(search_frame)
        self.tamir_arama.pack(side="left", fill="x", expand=True, padx=5)
        self.tamir_arama.bind('<KeyRelease>', self.tamir_arama_yap)
        self.show_tooltip(self.tamir_arama, "Müşteri adı, cihaz veya sorun ile arama yapın")
        
        # Tamir listesi
        columns = ("id", "musteri", "cihaz", "sorun", "tarih", "maliyet", "durum")
        self.tamir_tree = ttk.Treeview(right_panel, columns=columns, show="headings")
        
        # Sütun başlıkları
        self.tamir_tree.heading("id", text="ID")
        self.tamir_tree.heading("musteri", text="Müşteri")
        self.tamir_tree.heading("cihaz", text="Cihaz")
        self.tamir_tree.heading("sorun", text="Sorun")
        self.tamir_tree.heading("tarih", text="Tarih")
        self.tamir_tree.heading("maliyet", text="Maliyet")
        self.tamir_tree.heading("durum", text="Durum")
        
        # Sütun genişlikleri
        self.tamir_tree.column("id", width=50)
        self.tamir_tree.column("musteri", width=150)
        self.tamir_tree.column("cihaz", width=120)
        self.tamir_tree.column("sorun", width=200)
        self.tamir_tree.column("tarih", width=100)
        self.tamir_tree.column("maliyet", width=100)
        self.tamir_tree.column("durum", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.tamir_tree.yview)
        self.tamir_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid yapılandırması
        self.tamir_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Çift tıklama olayı
        self.tamir_tree.bind("<Double-1>", self.tamir_sec)
        
        # Tamir listesini güncelle
        self.tamir_liste_guncelle()
        
        # Müşteri listesini güncelle
        self.musteri_listesini_guncelle()
        
    def tamir_form_temizle(self):
        """Tamir formunu temizler"""
        self.tamir_musteri.set("")
        self.tamir_cihaz.delete(0, tk.END)
        self.tamir_sorun.delete("1.0", tk.END)
        self.tamir_maliyet.delete(0, tk.END)
        self.tamir_durum.set("Açık")
        self.tamir_tree.selection_remove(self.tamir_tree.selection())
        
    def tamir_kaydet(self):
        """Tamir bilgilerini kaydeder"""
        try:
            musteri = self.tamir_musteri.get()
            cihaz = self.tamir_cihaz.get().strip()
            sorun = self.tamir_sorun.get("1.0", tk.END).strip()
            maliyet = self.tamir_maliyet.get().strip()
            durum = self.tamir_durum.get()
            
            if not musteri or not cihaz or not sorun:
                self.show_notification("Uyarı", "Müşteri, cihaz ve sorun alanları zorunludur", "warning")
                return
                
            # Müşteri ID'sini al
            self.cursor.execute("SELECT id FROM musteriler WHERE ad=?", (musteri,))
            musteri_id = self.cursor.fetchone()[0]
            
            # Maliyeti sayıya çevir
            try:
                maliyet = float(maliyet) if maliyet else 0.0
            except ValueError:
                self.show_notification("Uyarı", "Geçersiz maliyet değeri", "warning")
                return
            
            selected_item = self.tamir_tree.selection()
            if selected_item:
                # Güncelleme
                tamir_id = self.tamir_tree.item(selected_item)['values'][0]
                self.cursor.execute("""
                    UPDATE tamirler 
                    SET musteri_id=?, cihaz=?, sorun=?, maliyet=?, durum=?
                    WHERE id=?
                """, (musteri_id, cihaz, sorun, maliyet, durum, tamir_id))
            else:
                # Yeni kayıt
                self.cursor.execute("""
                    INSERT INTO tamirler (musteri_id, cihaz, sorun, tarih, maliyet, durum)
                    VALUES (?, ?, ?, datetime('now'), ?, ?)
                """, (musteri_id, cihaz, sorun, maliyet, durum))
                
            self.conn.commit()
            self.tamir_liste_guncelle()
            self.tamir_form_temizle()
            self.show_notification("Başarılı", "Tamir bilgileri kaydedildi", "success")
            self.aktivite_kaydet("Tamir Kaydı", f"Cihaz: {cihaz}")
        except Exception as e:
            logger.error(f"Tamir kaydedilirken hata: {str(e)}")
            self.show_notification("Hata", "Tamir kaydedilemedi", "error")
            
    def tamir_sec(self, event):
        """Tamir listesinden seçilen kaydı forma yükler"""
        selected_item = self.tamir_tree.selection()
        if selected_item:
            values = self.tamir_tree.item(selected_item)['values']
            self.tamir_musteri.set(values[1])  # Müşteri adı
            self.tamir_cihaz.delete(0, tk.END)
            self.tamir_cihaz.insert(0, values[2])
            self.tamir_sorun.delete("1.0", tk.END)
            self.tamir_sorun.insert("1.0", values[3])
            self.tamir_maliyet.delete(0, tk.END)
            self.tamir_maliyet.insert(0, values[5])
            self.tamir_durum.set(values[6])
            
    def tamir_arama_yap(self, event):
        """Tamir listesinde arama yapar"""
        search_term = self.tamir_arama.get().lower()
        for item in self.tamir_tree.get_children():
            values = self.tamir_tree.item(item)['values']
            if (search_term in values[1].lower() or  # Müşteri adı
                search_term in values[2].lower() or  # Cihaz
                search_term in values[3].lower()):   # Sorun
                self.tamir_tree.selection_set(item)
                self.tamir_tree.see(item)
            else:
                self.tamir_tree.selection_remove(item)
                
    def tamir_liste_guncelle(self):
        """Tamir listesini günceller"""
        # Mevcut öğeleri temizle
        for item in self.tamir_tree.get_children():
            self.tamir_tree.delete(item)
            
        try:
            self.cursor.execute('''
                SELECT t.id, m.ad, t.cihaz, t.sorun, t.tarih, t.maliyet, t.durum
                FROM tamirler t
                JOIN musteriler m ON t.musteri_id = m.id
                ORDER BY t.tarih DESC
            ''')
            for row in self.cursor.fetchall():
                self.tamir_tree.insert("", "end", values=row)
        except Exception as e:
            logger.error(f"Tamir listesi güncellenirken hata: {str(e)}")
            self.show_notification("Hata", "Tamir listesi güncellenemedi", "error")
            
    def musteri_listesini_guncelle(self):
        """Müşteri listesini günceller"""
        try:
            self.cursor.execute("SELECT ad FROM musteriler ORDER BY ad")
            musteriler = [row[0] for row in self.cursor.fetchall()]
            self.tamir_musteri['values'] = musteriler
        except Exception as e:
            logger.error(f"Müşteri listesi güncellenirken hata: {str(e)}")
            self.show_notification("Hata", "Müşteri listesi güncellenemedi", "error")
    
    def yeni_musteri(self):
        dialog = MusteriDialog(self.root, "Yeni Müşteri")
        if dialog.result:
            musteri = Musteri(
                ad=dialog.result["ad"],
                soyad=dialog.result["soyad"],
                telefon=dialog.result["telefon"],
                email=dialog.result["email"],
                adres=dialog.result["adres"]
            )
            if self.db.musteri_ekle(musteri):
                self.musteri_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Müşteri başarıyla eklendi.")
            else:
                messagebox.showerror("Hata", "Müşteri eklenirken bir hata oluştu.")
    
    def musteri_duzenle(self):
        selection = self.musteri_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen düzenlenecek müşteriyi seçin.")
            return
            
        item = self.musteri_listesi.item(selection[0])
        musteri = Musteri(
            id=item["values"][0],
            ad=item["values"][1],
            soyad=item["values"][2],
            telefon=item["values"][3],
            email=item["values"][4],
            adres=item["values"][5]
        )
        
        dialog = MusteriDialog(self.root, "Müşteri Düzenle", musteri)
        if dialog.result:
            musteri.ad = dialog.result["ad"]
            musteri.soyad = dialog.result["soyad"]
            musteri.telefon = dialog.result["telefon"]
            musteri.email = dialog.result["email"]
            musteri.adres = dialog.result["adres"]
            
            if self.db.musteri_guncelle(musteri):
                self.musteri_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Müşteri başarıyla güncellendi.")
            else:
                messagebox.showerror("Hata", "Müşteri güncellenirken bir hata oluştu.")
    
    def musteri_sil(self):
        selection = self.musteri_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen silinecek müşteriyi seçin.")
            return
            
        if messagebox.askyesno("Onay", "Seçili müşteriyi silmek istediğinizden emin misiniz?"):
            item = self.musteri_listesi.item(selection[0])
            if self.db.musteri_sil(item["values"][0]):
                self.musteri_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Müşteri başarıyla silindi.")
            else:
                messagebox.showerror("Hata", "Müşteri silinirken bir hata oluştu.")
    
    def tamir_ekle(self):
        selection = self.musteri_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen tamir eklenecek müşteriyi seçin.")
            return
            
        item = self.musteri_listesi.item(selection[0])
        musteri_id = item["values"][0]
        
        dialog = TamirDialog(self.root, "Yeni Tamir", musteri_id)
        if dialog.result:
            tamir = Tamir(
                musteri_id=musteri_id,
                cihaz=dialog.result["cihaz"],
                sorun=dialog.result["sorun"],
                tarih=datetime.now().strftime("%Y-%m-%d"),
                maliyet=dialog.result["maliyet"],
                durum="Açık"
            )
            if self.db.tamir_ekle(tamir):
                messagebox.showinfo("Başarılı", "Tamir kaydı başarıyla eklendi.")
            else:
                messagebox.showerror("Hata", "Tamir kaydı eklenirken bir hata oluştu.")
    
    def musteri_ara(self):
        anahtar_kelime = self.musteri_arama_entry.get()
        
        # Mevcut listeyi temizle
        for item in self.musteri_listesi.get_children():
            self.musteri_listesi.delete(item)
            
        try:
            # Arama sonuçlarını listele
            musteriler = self.db.musteri_ara(anahtar_kelime)
            if not musteriler:
                messagebox.showinfo("Bilgi", "Arama kriterlerine uygun müşteri bulunamadı.")
                return
                
            for musteri in musteriler:
                self.musteri_listesi.insert("", "end", values=(
                    musteri.id, musteri.ad, musteri.soyad, musteri.telefon, 
                    musteri.email, musteri.adres
                ))
            messagebox.showinfo("Bilgi", f"{len(musteriler)} müşteri bulundu.")
        except Exception as e:
            print(f"Müşteri arama hatası: {e}")
            messagebox.showerror("Hata", "Müşteri arama sırasında bir hata oluştu.")
    
    def rapor_goster(self):
        dialog = RaporDialog(self.root, self.db)
        dialog.wait_window()

    def tamir_listesini_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.tamir_listesi.get_children():
            self.tamir_listesi.delete(item)
            
        # Veritabanından tamirleri al ve listeye ekle
        try:
            self.cursor.execute('''
                SELECT t.id, m.ad, t.cihaz, t.sorun, t.tarih, t.maliyet, t.durum
                FROM tamirler t
                JOIN musteriler m ON t.musteri_id = m.id
                ORDER BY t.tarih DESC
            ''')
            for row in self.cursor.fetchall():
                self.tamir_listesi.insert("", "end", values=row)
        except sqlite3.Error as e:
            print(f"Tamir listesi güncelleme hatası: {e}")
    
    def tamir_ara(self):
        anahtar_kelime = self.tamir_arama_entry.get()
        
        # Mevcut listeyi temizle
        for item in self.tamir_listesi.get_children():
            self.tamir_listesi.delete(item)
            
        try:
            # Arama sonuçlarını listele
            self.cursor.execute('''
                SELECT t.id, m.ad, t.cihaz, t.sorun, t.tarih, t.maliyet, t.durum
                FROM tamirler t
                JOIN musteriler m ON t.musteri_id = m.id
                WHERE m.ad LIKE ? OR t.cihaz LIKE ? OR t.sorun LIKE ?
                ORDER BY t.tarih DESC
            ''', (f'%{anahtar_kelime}%', f'%{anahtar_kelime}%', f'%{anahtar_kelime}%'))
            
            sonuclar = self.cursor.fetchall()
            if not sonuclar:
                messagebox.showinfo("Bilgi", "Arama kriterlerine uygun tamir kaydı bulunamadı.")
                return
                
            for row in sonuclar:
                self.tamir_listesi.insert("", "end", values=row)
            messagebox.showinfo("Bilgi", f"{len(sonuclar)} tamir kaydı bulundu.")
        except Exception as e:
            print(f"Tamir arama hatası: {e}")
            messagebox.showerror("Hata", "Tamir arama sırasında bir hata oluştu.")
    
    def tamir_duzenle(self):
        selection = self.tamir_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen düzenlenecek tamiri seçin.")
            return
            
        item = self.tamir_listesi.item(selection[0])
        tamir_id = item["values"][0]
        
        try:
            self.cursor.execute('''
                SELECT * FROM tamirler WHERE id=?
            ''', (tamir_id,))
            tamir_data = self.cursor.fetchone()
            
            if tamir_data:
                tamir = Tamir(*tamir_data)
                dialog = TamirDialog(self.root, "Tamir Düzenle", tamir)
                if dialog.result:
                    tamir.cihaz = dialog.result["cihaz"]
                    tamir.sorun = dialog.result["sorun"]
                    tamir.maliyet = dialog.result["maliyet"]
                    tamir.durum = dialog.result.get("durum", tamir.durum)
                    
                    if self.db.tamir_guncelle(tamir):
                        self.tamir_listesini_guncelle()
                        messagebox.showinfo("Başarılı", "Tamir başarıyla güncellendi.")
                    else:
                        messagebox.showerror("Hata", "Tamir güncellenirken bir hata oluştu.")
        except sqlite3.Error as e:
            print(f"Tamir düzenleme hatası: {e}")
            messagebox.showerror("Hata", "Tamir güncellenirken bir hata oluştu.")
    
    def tamir_sil(self):
        selection = self.tamir_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen silinecek tamiri seçin.")
            return
            
        if messagebox.askyesno("Onay", "Seçili tamiri silmek istediğinizden emin misiniz?"):
            item = self.tamir_listesi.item(selection[0])
            tamir_id = item["values"][0]
            
            try:
                self.cursor.execute('DELETE FROM tamirler WHERE id=?', (tamir_id,))
                self.conn.commit()
                self.tamir_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Tamir başarıyla silindi.")
            except sqlite3.Error as e:
                print(f"Tamir silme hatası: {e}")
                messagebox.showerror("Hata", "Tamir silinirken bir hata oluştu.")
    
    def maliyet_tahmini(self):
        selection = self.tamir_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen maliyet tahmini yapılacak tamiri seçin.")
            return
            
        item = self.tamir_listesi.item(selection[0])
        tamir_id = item["values"][0]
        
        dialog = MaliyetTahminiDialog(self.root, tamir_id)
        if dialog.result:
            if self.db.maliyet_tahmini_ekle(dialog.result):
                messagebox.showinfo("Başarılı", "Maliyet tahmini başarıyla kaydedildi.")
            else:
                messagebox.showerror("Hata", "Maliyet tahmini kaydedilirken bir hata oluştu.")

    def yeni_tamir(self):
        """Yeni tamir kaydı oluşturur"""
        # Önce müşteri seçimi yapılmalı
        selection = self.musteri_listesi.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen önce bir müşteri seçin.")
            return
            
        item = self.musteri_listesi.item(selection[0])
        musteri_id = item["values"][0]
        
        dialog = TamirDialog(self.root, "Yeni Tamir", musteri_id)
        if dialog.result:
            tamir = Tamir(
                musteri_id=musteri_id,
                cihaz=dialog.result["cihaz"],
                sorun=dialog.result["sorun"],
                tarih=datetime.now().strftime("%Y-%m-%d"),
                maliyet=dialog.result["maliyet"],
                durum="Açık"
            )
            if self.db.tamir_ekle(tamir):
                self.tamir_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Tamir kaydı başarıyla eklendi.")
            else:
                messagebox.showerror("Hata", "Tamir kaydı eklenirken bir hata oluştu.")

    def ayarlar_sekmesi_olustur(self):
        # Ana panel
        main_panel = ttk.Frame(self.ayarlar_frame, padding="20")
        main_panel.pack(fill="both", expand=True)
        
        # Sol panel - Genel ayarlar
        left_panel = ttk.LabelFrame(main_panel, text="Genel Ayarlar", padding="20")
        left_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Dil ayarları
        dil_frame = ttk.LabelFrame(left_panel, text="Dil Ayarları", padding="10")
        dil_frame.pack(fill="x", pady=5)
        
        ttk.Label(dil_frame, text="Dil:").pack(side="left", padx=5)
        self.dil_secim = ttk.Combobox(dil_frame, values=["Türkçe", "English"], state="readonly")
        self.dil_secim.pack(side="left", fill="x", expand=True, padx=5)
        self.dil_secim.set("Türkçe")
        self.show_tooltip(self.dil_secim, "Uygulama dilini seçiniz")
        
        # Tema ayarları
        tema_frame = ttk.LabelFrame(left_panel, text="Tema Ayarları", padding="10")
        tema_frame.pack(fill="x", pady=5)
        
        ttk.Label(tema_frame, text="Tema:").pack(side="left", padx=5)
        self.tema_secim = ttk.Combobox(tema_frame, values=["arc", "equilux", "adapta"], state="readonly")
        self.tema_secim.pack(side="left", fill="x", expand=True, padx=5)
        self.tema_secim.set("arc")
        self.show_tooltip(self.tema_secim, "Uygulama temasını seçiniz")
        
        # Sağ panel - E-posta ayarları
        right_panel = ttk.LabelFrame(main_panel, text="E-posta Ayarları", padding="20")
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # E-posta formu
        email_form = ttk.Frame(right_panel)
        email_form.pack(fill="both", expand=True)
        
        # E-posta adresi
        ttk.Label(email_form, text="E-posta:").grid(row=0, column=0, sticky="w", pady=5)
        self.email_adres = ttk.Entry(email_form, width=30)
        self.email_adres.grid(row=0, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.email_adres, "Gmail adresinizi giriniz")
        
        # Uygulama şifresi
        ttk.Label(email_form, text="Uygulama Şifresi:").grid(row=1, column=0, sticky="w", pady=5)
        self.email_sifre = ttk.Entry(email_form, width=30, show="*")
        self.email_sifre.grid(row=1, column=1, sticky="ew", pady=5)
        self.show_tooltip(self.email_sifre, "Gmail uygulama şifrenizi giriniz")
        
        # Yedekleme sıklığı
        ttk.Label(email_form, text="Yedekleme Sıklığı:").grid(row=2, column=0, sticky="w", pady=5)
        self.yedekleme_sikligi = ttk.Combobox(email_form, width=30, 
                                            values=["Günlük", "Haftalık", "Aylık"], 
                                            state="readonly")
        self.yedekleme_sikligi.grid(row=2, column=1, sticky="ew", pady=5)
        self.yedekleme_sikligi.set("Günlük")
        self.show_tooltip(self.yedekleme_sikligi, "Yedekleme sıklığını seçiniz")
        
        # Butonlar
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill="x", pady=10)
        
        self.ayarlar_kaydet_btn = ttk.Button(button_frame, text="Kaydet", 
                                           image=self.icons["save"], compound="left",
                                           command=self.ayarlar_kaydet)
        self.ayarlar_kaydet_btn.pack(side="left", padx=5)
        self.show_tooltip(self.ayarlar_kaydet_btn, "Ayarları kaydet")
        
        self.ayarlar_test_btn = ttk.Button(button_frame, text="Test Et",
                                         image=self.icons["test"], compound="left",
                                         command=self.email_test)
        self.ayarlar_test_btn.pack(side="left", padx=5)
        self.show_tooltip(self.ayarlar_test_btn, "E-posta ayarlarını test et")
        
        # Ayarları yükle
        self.ayarlar_yukle()
        
    def ayarlar_yukle(self):
        try:
            self.cursor.execute("SELECT * FROM ayarlar")
            ayarlar = self.cursor.fetchone()
            if ayarlar:
                self.dil_secim.set(ayarlar[1])
                self.tema_secim.set(ayarlar[2])
                self.email_adres.insert(0, ayarlar[3])
                self.email_sifre.insert(0, ayarlar[4])
                self.yedekleme_sikligi.set(ayarlar[5])
        except Exception as e:
            logger.error(f"Ayarlar yüklenirken hata: {str(e)}")
            self.show_notification("Hata", "Ayarlar yüklenemedi", "error")
            
    def ayarlar_kaydet(self):
        try:
            dil = self.dil_secim.get()
            tema = self.tema_secim.get()
            email = self.email_adres.get().strip()
            sifre = self.email_sifre.get().strip()
            siklik = self.yedekleme_sikligi.get()
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO ayarlar (id, dil, tema, email, sifre, yedekleme_sikligi)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (dil, tema, email, sifre, siklik))
            
            self.conn.commit()
            self.show_notification("Başarılı", "Ayarlar kaydedildi", "success")
            self.aktivite_kaydet("Ayarlar", "Ayarlar güncellendi")
            
            # Tema değişikliğini uygula
            if tema != self.root.tk.call("ttk::style", "theme", "use"):
                self.root.tk.call("ttk::style", "theme", "use", tema)
                
        except Exception as e:
            logger.error(f"Ayarlar kaydedilirken hata: {str(e)}")
            self.show_notification("Hata", "Ayarlar kaydedilemedi", "error")
            
    def email_test(self):
        try:
            email = self.email_adres.get().strip()
            sifre = self.email_sifre.get().strip()
            
            if not email or not sifre:
                self.show_notification("Uyarı", "E-posta ve şifre alanları boş bırakılamaz", "warning")
                return
                
            # Test e-postası gönder
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email
            msg['Subject'] = "Tamir Atölyesi - E-posta Testi"
            
            body = "Bu bir test e-postasıdır. E-posta ayarlarınız başarıyla çalışıyor."
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, sifre)
            server.send_message(msg)
            server.quit()
            
            self.show_notification("Başarılı", "Test e-postası gönderildi", "success")
            self.aktivite_kaydet("E-posta Testi", "Test e-postası gönderildi")
            
        except Exception as e:
            logger.error(f"E-posta testi sırasında hata: {str(e)}")
            self.show_notification("Hata", "E-posta testi başarısız", "error")

    def email_ayarlari_goster(self):
        """E-posta ayarları penceresini gösterir"""
        dialog = EmailAyarlariDialog(self.root)
        dialog.wait_window()
        
        # Ayarlar değiştiyse yedekleme yöneticisini güncelle
        if dialog.result:
            try:
                yedek_yoneticisi = YedekYoneticisi()
                yedek_yoneticisi.email_ayarlarini_guncelle(
                    dialog.result["email"],
                    dialog.result["sifre"],
                    dialog.result["email"],  # Kendine gönder
                    dialog.result["siklik"]
                )
                self.show_notification("Başarılı", "E-posta ayarları güncellendi", "success")
                self.aktivite_kaydet("Ayarlar", "E-posta ayarları güncellendi")
            except Exception as e:
                logger.error(f"E-posta ayarları güncellenirken hata: {str(e)}")
                self.show_notification("Hata", "E-posta ayarları güncellenemedi", "error")

    def center_window(self):
        """Pencereyi ekranın ortasına konumlandırır"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
    
class MusteriDialog:
    def __init__(self, parent, title, musteri=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Dialog için grid yapılandırması
        self.dialog.grid_rowconfigure(5, weight=1)
        self.dialog.grid_columnconfigure(1, weight=1)
        
        self.result = None
        
        # Form alanları
        ttk.Label(self.dialog, text="Ad:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.ad_entry = ttk.Entry(self.dialog, width=40)
        self.ad_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Soyad:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.soyad_entry = ttk.Entry(self.dialog, width=40)
        self.soyad_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Telefon:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.telefon_entry = ttk.Entry(self.dialog, width=40)
        self.telefon_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Email:", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.email_entry = ttk.Entry(self.dialog, width=40)
        self.email_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Adres:", font=("Arial", 10, "bold")).grid(row=4, column=0, padx=10, pady=10, sticky="nw")
        self.adres_text = tk.Text(self.dialog, width=40, height=5)
        self.adres_text.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        
        # Mevcut müşteri bilgilerini doldur
        if musteri:
            self.ad_entry.insert(0, musteri.ad)
            self.soyad_entry.insert(0, musteri.soyad)
            self.telefon_entry.insert(0, musteri.telefon)
            self.email_entry.insert(0, musteri.email or "")
            self.adres_text.insert("1.0", musteri.adres or "")
        
        # Butonlar çerçevesi
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        button_frame.grid_columnconfigure((0,1), weight=1)
        
        ttk.Button(button_frame, text="Kaydet", command=self.kaydet).grid(row=0, column=0, padx=10, sticky="ew")
        ttk.Button(button_frame, text="İptal", command=self.dialog.destroy).grid(row=0, column=1, padx=10, sticky="ew")
        
        self.dialog.wait_window()
    
    def kaydet(self):
        ad = self.ad_entry.get().strip()
        soyad = self.soyad_entry.get().strip()
        telefon = self.telefon_entry.get().strip()
        email = self.email_entry.get().strip()
        adres = self.adres_text.get("1.0", tk.END).strip()
        
        if not ad or not soyad or not telefon:
            messagebox.showerror("Hata", "Ad, soyad ve telefon alanları zorunludur.")
            return
            
        self.result = {
            "ad": ad,
            "soyad": soyad,
            "telefon": telefon,
            "email": email,
            "adres": adres
        }
        self.dialog.destroy()

class TamirDialog:
    def __init__(self, parent, title, musteri_id=None, tamir=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x500")  # Pencere boyutunu büyüttük
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Dialog için grid yapılandırması
        self.dialog.grid_rowconfigure(5, weight=1)
        self.dialog.grid_columnconfigure(1, weight=1)
        
        self.result = None
        self.musteri_id = musteri_id
        
        # Müşteri ID kontrolü
        if not musteri_id and not tamir:
            messagebox.showerror("Hata", "Tamir kaydı için müşteri seçimi gereklidir.")
            self.dialog.destroy()
            return
        
        # Müşteri bilgilerini göster
        musteri_frame = ttk.LabelFrame(self.dialog, text="Müşteri Bilgileri", padding="10")
        musteri_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Müşteri bilgilerini al
        if musteri_id:
            try:
                cursor = parent.db.cursor
                cursor.execute('SELECT ad, soyad, telefon FROM musteriler WHERE id=?', (musteri_id,))
                musteri = cursor.fetchone()
                if musteri:
                    ttk.Label(musteri_frame, text=f"Ad Soyad: {musteri[0]} {musteri[1]}", font=("Arial", 10, "bold")).pack(anchor="w")
                    ttk.Label(musteri_frame, text=f"Telefon: {musteri[2]}", font=("Arial", 10, "bold")).pack(anchor="w")
            except Exception as e:
                logger.error(f"Müşteri bilgileri alınırken hata: {str(e)}")
        
        # Form alanları
        ttk.Label(self.dialog, text="Cihaz:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.cihaz_entry = ttk.Entry(self.dialog, width=40)
        self.cihaz_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Sorun:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        self.sorun_text = tk.Text(self.dialog, width=40, height=5)
        self.sorun_text.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Maliyet:", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.maliyet_entry = ttk.Entry(self.dialog, width=40)
        self.maliyet_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Durum:", font=("Arial", 10, "bold")).grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.durum_combo = ttk.Combobox(self.dialog, values=["Açık", "Devam Ediyor", "Tamamlandı", "İptal"], state="readonly")
        self.durum_combo.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.durum_combo.set("Açık")
        
        # Mevcut tamir bilgilerini doldur
        if tamir:
            self.cihaz_entry.insert(0, tamir.cihaz)
            self.sorun_text.insert("1.0", tamir.sorun)
            self.maliyet_entry.insert(0, str(tamir.maliyet or ""))
            self.durum_combo.set(tamir.durum)
            self.musteri_id = tamir.musteri_id
        
        # Butonlar çerçevesi
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        button_frame.grid_columnconfigure((0,1), weight=1)
        
        ttk.Button(button_frame, text="Kaydet", command=self.kaydet).grid(row=0, column=0, padx=10, sticky="ew")
        ttk.Button(button_frame, text="İptal", command=self.dialog.destroy).grid(row=0, column=1, padx=10, sticky="ew")
        
        self.dialog.wait_window()
    
    def kaydet(self):
        cihaz = self.cihaz_entry.get().strip()
        sorun = self.sorun_text.get("1.0", tk.END).strip()
        maliyet = self.maliyet_entry.get().strip()
        durum = self.durum_combo.get()
        
        if not cihaz or not sorun:
            messagebox.showerror("Hata", "Cihaz ve sorun alanları zorunludur.")
            return
            
        try:
            maliyet = float(maliyet) if maliyet else 0.0
        except ValueError:
            messagebox.showerror("Hata", "Maliyet geçerli bir sayı olmalıdır.")
            return
            
        self.result = {
            "musteri_id": self.musteri_id,
            "cihaz": cihaz,
            "sorun": sorun,
            "maliyet": maliyet,
            "durum": durum
        }
        self.dialog.destroy()

class MaliyetTahminiDialog:
    def __init__(self, parent, tamir_id):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Maliyet Tahmini")
        self.dialog.geometry("500x400")
        
        self.tamir_id = tamir_id
        self.result = None
        
        # Grid yapılandırması
        self.dialog.grid_rowconfigure(4, weight=1)
        self.dialog.grid_columnconfigure(1, weight=1)
        
        # Form alanları
        ttk.Label(self.dialog, text="İşçilik Maliyeti (TL):", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.iscilik_entry = ttk.Entry(self.dialog, width=30)
        self.iscilik_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Malzeme Maliyeti (TL):", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.malzeme_entry = ttk.Entry(self.dialog, width=30)
        self.malzeme_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Açıklama:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        self.aciklama_text = tk.Text(self.dialog, width=30, height=5)
        self.aciklama_text.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # Butonlar
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        button_frame.grid_columnconfigure((0,1), weight=1)
        
        ttk.Button(button_frame, text="Kaydet", command=self.kaydet).grid(row=0, column=0, padx=10, sticky="ew")
        ttk.Button(button_frame, text="İptal", command=self.dialog.destroy).grid(row=0, column=1, padx=10, sticky="ew")
        
        self.dialog.wait_window()
    
    def kaydet(self):
        try:
            iscilik = float(self.iscilik_entry.get())
            malzeme = float(self.malzeme_entry.get())
            toplam = iscilik + malzeme
            aciklama = self.aciklama_text.get("1.0", tk.END).strip()
            
            self.result = MaliyetTahmini(
                tamir_id=self.tamir_id,
                iscilik_maliyeti=iscilik,
                malzeme_maliyeti=malzeme,
                toplam_maliyet=toplam,
                onay_durumu="Beklemede",
                aciklama=aciklama,
                tarih=datetime.now().strftime("%Y-%m-%d")
            )
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler giriniz.")

class RaporDialog(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("Rapor Oluştur")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Ana frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Rapor türü seçimi
        ttk.Label(main_frame, text="Rapor Türü:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.rapor_turu = ttk.Combobox(main_frame, values=[
            "Tamir Raporu - Tüm Kayıtlar",
            "Tamir Raporu - Tamamlanan İşler",
            "Tamir Raporu - Devam Eden İşler",
            "Müşteri Bazlı Tamir Raporu",
            "Maliyet Analiz Raporu"
        ], state="readonly", width=40)
        self.rapor_turu.set("Tamir Raporu - Tüm Kayıtlar")
        self.rapor_turu.pack(fill="x", pady=(0, 10))
        
        # Tarih seçimi frame
        date_frame = ttk.LabelFrame(main_frame, text="Tarih Aralığı", padding="10")
        date_frame.pack(fill="x", pady=(0, 10))
        
        # Başlangıç tarihi
        ttk.Label(date_frame, text="Başlangıç:").grid(row=0, column=0, padx=5, pady=5)
        self.baslangic_tarihi = DateEntry(
            date_frame,
            width=20,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            locale='tr_TR'
        )
        self.baslangic_tarihi.grid(row=0, column=1, padx=5, pady=5)
        
        # Bitiş tarihi
        ttk.Label(date_frame, text="Bitiş:").grid(row=1, column=0, padx=5, pady=5)
        self.bitis_tarihi = DateEntry(
            date_frame,
            width=20,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            locale='tr_TR'
        )
        self.bitis_tarihi.grid(row=1, column=1, padx=5, pady=5)
        
        # Rapor formatı
        format_frame = ttk.LabelFrame(main_frame, text="Rapor Formatı", padding="10")
        format_frame.pack(fill="x", pady=(0, 10))
        
        self.rapor_format = tk.StringVar(value="pdf")
        ttk.Radiobutton(format_frame, text="PDF", variable=self.rapor_format, value="pdf").pack(side="left", padx=20)
        ttk.Radiobutton(format_frame, text="Excel", variable=self.rapor_format, value="excel").pack(side="left", padx=20)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Rapor Oluştur", command=self.rapor_olustur, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="İptal", command=self.destroy, width=20).pack(side="left", padx=5)
    
    def rapor_olustur(self):
        try:
            # Tarih formatını kontrol et
            try:
                baslangic = self.baslangic_tarihi.get_date().strftime("%Y-%m-%d")
                bitis = self.bitis_tarihi.get_date().strftime("%Y-%m-%d")
            except Exception as e:
                messagebox.showerror("Hata", "Geçersiz tarih formatı!")
                return
            
            # Rapor türünü belirle
            rapor_turu = self.rapor_turu.get()
            durum = None
            if "Tamamlanan İşler" in rapor_turu:
                durum = "Tamamlandı"
            elif "Devam Eden İşler" in rapor_turu:
                durum = "Devam Ediyor"
            
            # Rapor verilerini al
            if "Müşteri Bazlı" in rapor_turu:
                veriler = self.db.musteri_bazli_tamir_raporu(baslangic, bitis)
            elif "Maliyet Analiz" in rapor_turu:
                veriler = self.db.maliyet_analiz_raporu(baslangic, bitis)
            else:
                veriler = self.db.musteri_tamir_raporu(baslangic, bitis, durum)
            
            if not veriler:
                messagebox.showwarning("Uyarı", "Seçilen tarih aralığında veri bulunamadı!")
                return
            
            # Rapor oluştur
            if self.rapor_format.get() == "pdf":
                self.pdf_raporu_olustur(veriler, rapor_turu, baslangic, bitis)
            else:
                self.excel_raporu_olustur(veriler, rapor_turu, baslangic, bitis)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken bir hata oluştu:\n{str(e)}")
    
    def pdf_raporu_olustur(self, veriler, rapor_turu, baslangic, bitis):
        try:
            # Rapor dosyası oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dosya_adi = f"{rapor_turu.lower().replace(' ', '_')}_{timestamp}.pdf"
            dosya_yolu = REPORT_DIR / dosya_adi
            
            # PDF oluştur
            pdf = FPDF()
            pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            pdf.set_font('DejaVu', '', 12)
            
            # Başlık sayfası
            pdf.add_page()
            pdf.set_font('DejaVu', '', 16)
            pdf.cell(0, 10, rapor_turu, ln=True, align="C")
            pdf.set_font('DejaVu', '', 12)
            pdf.cell(0, 10, f"Tarih Aralığı: {baslangic} - {bitis}", ln=True)
            pdf.cell(0, 10, f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)
            
            # Rapor içeriği
            pdf.add_page()
            if "Müşteri Bazlı" in rapor_turu:
                self._musteri_bazli_pdf_rapor(pdf, veriler)
            elif "Maliyet Analiz" in rapor_turu:
                self._maliyet_analiz_pdf_rapor(pdf, veriler)
            else:
                self._tamir_pdf_rapor(pdf, veriler)
            
            # PDF'i kaydet
            pdf.output(str(dosya_yolu))
            
            # Raporu aç
            os.startfile(dosya_yolu)
            messagebox.showinfo("Başarılı", f"Rapor oluşturuldu:\n{dosya_yolu}")
            
        except Exception as e:
            raise Exception(f"PDF raporu oluşturulurken hata: {str(e)}")
    
    def excel_raporu_olustur(self, veriler, rapor_turu, baslangic, bitis):
        try:
            # Rapor dosyası oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dosya_adi = f"{rapor_turu.lower().replace(' ', '_')}_{timestamp}.xlsx"
            dosya_yolu = REPORT_DIR / dosya_adi
            
            # Excel verilerini hazırla
            if "Müşteri Bazlı" in rapor_turu:
                df = pd.DataFrame(veriler, columns=[
                    'Müşteri ID', 'Ad', 'Soyad', 'Telefon', 'E-posta', 'Adres',
                    'Tamir Sayısı', 'Toplam İşçilik', 'Toplam Parça', 'Genel Toplam'
                ])
            elif "Maliyet Analiz" in rapor_turu:
                df = pd.DataFrame(veriler, columns=[
                    'Tamir ID', 'Müşteri Adı', 'Cihaz', 'Sorun', 'Giriş Tarihi',
                    'İşçilik Ücreti', 'Parça Ücreti', 'Toplam Ücret', 'Kullanılan Parçalar'
                ])
            else:
                df = pd.DataFrame(veriler, columns=[
                    'Tamir ID', 'Müşteri Adı', 'Cihaz', 'Sorun', 'Giriş Tarihi',
                    'Durum', 'İşçilik Ücreti', 'Parça Ücreti', 'Toplam Ücret'
                ])
            
            # Excel'e kaydet
            df.to_excel(dosya_yolu, index=False, sheet_name=rapor_turu[:31])
            
            # Raporu aç
            os.startfile(dosya_yolu)
            messagebox.showinfo("Başarılı", f"Rapor oluşturuldu:\n{dosya_yolu}")
            
        except Exception as e:
            raise Exception(f"Excel raporu oluşturulurken hata: {str(e)}")
    
    def _musteri_bazli_pdf_rapor(self, pdf, veriler):
        # Tablo başlıkları
        headers = ['Müşteri', 'Tamir Sayısı', 'Toplam İşçilik', 'Toplam Parça', 'Genel Toplam']
        col_widths = [60, 30, 30, 30, 30]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        
        # Tablo içeriği
        for veri in veriler:
            pdf.cell(60, 10, f"{veri[1]} {veri[2]}", 1)
            pdf.cell(30, 10, str(veri[6]), 1)
            pdf.cell(30, 10, f"{veri[7]:.2f} TL", 1)
            pdf.cell(30, 10, f"{veri[8]:.2f} TL", 1)
            pdf.cell(30, 10, f"{veri[9]:.2f} TL", 1)
            pdf.ln()
    
    def _maliyet_analiz_pdf_rapor(self, pdf, veriler):
        # Tablo başlıkları
        headers = ['Müşteri', 'Cihaz', 'İşçilik', 'Parça', 'Toplam']
        col_widths = [50, 50, 30, 30, 30]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        
        # Tablo içeriği
        for veri in veriler:
            pdf.cell(50, 10, veri[1], 1)
            pdf.cell(50, 10, veri[2], 1)
            pdf.cell(30, 10, f"{veri[3]:.2f} TL", 1)
            pdf.cell(30, 10, f"{veri[4]:.2f} TL", 1)
            pdf.cell(30, 10, f"{veri[5]:.2f} TL", 1)
            pdf.ln()
    
    def _tamir_pdf_rapor(self, pdf, veriler):
        # Tablo başlıkları
        headers = ['Tarih', 'Müşteri', 'Cihaz', 'Durum', 'Toplam']
        col_widths = [30, 50, 50, 30, 30]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        
        # Tablo içeriği
        for veri in veriler:
            pdf.cell(30, 10, veri[2].split()[0], 1)
            pdf.cell(50, 10, f"{veri[3]} {veri[4]}", 1)
            pdf.cell(50, 10, veri[5], 1)
            pdf.cell(30, 10, veri[6], 1)
            pdf.cell(30, 10, f"{veri[7]:.2f} TL", 1)
            pdf.ln()

class EmailAyarlariDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("E-posta Ayarları")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Dialog'u ekranın ortasına konumlandır
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')
        
        # Veritabanı bağlantısı
        self.conn = sqlite3.connect("tamir_atolyesi.db")
        self.cursor = self.conn.cursor()
        
        # Dialog için grid yapılandırması
        self.dialog.grid_rowconfigure(4, weight=1)
        self.dialog.grid_columnconfigure(1, weight=1)
        
        # E-posta ayarları
        ttk.Label(self.dialog, text="E-posta Adresi:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.email_entry = ttk.Entry(self.dialog, width=30)
        self.email_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Uygulama Şifresi:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = ttk.Entry(self.dialog, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        ttk.Label(self.dialog, text="Yedekleme Sıklığı:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.frequency_combo = ttk.Combobox(self.dialog, values=["Günlük", "Haftalık", "Aylık"], state="readonly")
        self.frequency_combo.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.frequency_combo.set("Günlük")
        
        # Butonlar
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Kaydet", command=self.kaydet).pack(side="left", padx=5)
        ttk.Button(button_frame, text="İptal", command=self.dialog.destroy).pack(side="left", padx=5)
        
        # Mevcut ayarları yükle
        self.ayarlari_yukle()
        
        # Dialog'u modal yap
        self.dialog.focus_set()
        self.dialog.grab_set()
        
        # Ana pencereyi gizle
        parent.withdraw()
        
        # Dialog kapandığında ana pencereyi tekrar göster
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(parent))
        
    def on_closing(self, parent):
        """Dialog kapatıldığında ana pencereyi tekrar gösterir"""
        self.dialog.destroy()
        parent.deiconify()
        
    def wait_window(self):
        """Dialog penceresinin kapanmasını bekler"""
        self.dialog.wait_window()
        
    def ayarlari_yukle(self):
        """Mevcut e-posta ayarlarını yükler"""
        try:
            self.cursor.execute("SELECT email, sifre, yedekleme_sikligi FROM ayarlar WHERE id=1")
            ayarlar = self.cursor.fetchone()
            if ayarlar:
                self.email_entry.insert(0, ayarlar[0])
                self.password_entry.insert(0, ayarlar[1])
                self.frequency_combo.set(ayarlar[2])
        except Exception as e:
            logger.error(f"E-posta ayarları yüklenirken hata: {str(e)}")
            
    def kaydet(self):
        """E-posta ayarlarını kaydeder"""
        try:
            email = self.email_entry.get().strip()
            password = self.password_entry.get().strip()
            frequency = self.frequency_combo.get()
            
            if not email or not password:
                messagebox.showerror("Hata", "E-posta ve şifre alanları zorunludur")
                return
                
            self.cursor.execute("""
                INSERT OR REPLACE INTO ayarlar (id, email, sifre, yedekleme_sikligi)
                VALUES (1, ?, ?, ?)
            """, (email, password, frequency))
            
            self.conn.commit()
            messagebox.showinfo("Başarılı", "E-posta ayarları kaydedildi")
            self.dialog.destroy()
        except Exception as e:
            logger.error(f"E-posta ayarları kaydedilirken hata: {str(e)}")
            messagebox.showerror("Hata", "E-posta ayarları kaydedilemedi")
            
    def __del__(self):
        """Veritabanı bağlantısını kapatır"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except Exception as e:
            logger.error(f"Veritabanı bağlantısı kapatılırken hata: {str(e)}")

class KullaniciAyarlariDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Kullanıcı Ayarları")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Form alanları
        ttk.Label(self.dialog, text="Mevcut Şifre:").grid(row=0, column=0, padx=10, pady=10)
        self.mevcut_sifre = ttk.Entry(self.dialog, show="*")
        self.mevcut_sifre.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(self.dialog, text="Yeni Şifre:").grid(row=1, column=0, padx=10, pady=10)
        self.yeni_sifre = ttk.Entry(self.dialog, show="*")
        self.yeni_sifre.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(self.dialog, text="Yeni Şifre (Tekrar):").grid(row=2, column=0, padx=10, pady=10)
        self.yeni_sifre_tekrar = ttk.Entry(self.dialog, show="*")
        self.yeni_sifre_tekrar.grid(row=2, column=1, padx=10, pady=10)
        
        # Butonlar
        ttk.Button(self.dialog, text="Şifre Değiştir", command=self.sifre_degistir).grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(self.dialog, text="Kapat", command=self.dialog.destroy).grid(row=4, column=0, columnspan=2)
    
    def sifre_degistir(self):
        """Kullanıcı şifresini değiştirir"""
        mevcut_sifre = self.mevcut_sifre.get()
        yeni_sifre = self.yeni_sifre.get()
        yeni_sifre_tekrar = self.yeni_sifre_tekrar.get()
        
        # TODO: Gerçek şifre değiştirme sistemi eklenecek
        # Şimdilik basit bir kontrol
        if mevcut_sifre != "1234":
            messagebox.showerror("Hata", "Mevcut şifre hatalı!")
            return
        
        if yeni_sifre != yeni_sifre_tekrar:
            messagebox.showerror("Hata", "Yeni şifreler eşleşmiyor!")
            return
        
        if len(yeni_sifre) < 4:
            messagebox.showerror("Hata", "Yeni şifre en az 4 karakter olmalıdır!")
            return
        
        messagebox.showinfo("Başarılı", "Şifre başarıyla değiştirildi!")
        self.dialog.destroy() 