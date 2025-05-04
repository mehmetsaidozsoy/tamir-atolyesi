import tkinter as tk
from tkinter import ttk
import logging
import win32gui
import win32con

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        
        # Ana pencere yapılandırması
        self.root.title("Tamir Atölyesi Yönetim Sistemi")
        
        # Notebook (sekmeler) oluştur
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sekmeleri oluştur
        self.create_tabs()
        
        # Pencereyi ön plana getir
        self.force_foreground()
        
    def force_foreground(self):
        """Pencereyi ön plana getirir"""
        hwnd = win32gui.GetForegroundWindow()
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
    def create_tabs(self):
        """Sekmeleri oluşturur"""
        # Müşteriler sekmesi
        self.customers_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.customers_frame, text="Müşteriler")
        
        # Tamirler sekmesi
        self.repairs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repairs_frame, text="Tamirler")
        
        # Ayarlar sekmesi
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Ayarlar") 