import tkinter as tk
from tkinter import ttk, messagebox
from database import VeritabaniYonetici

class MusteriYonetimi(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = VeritabaniYonetici()
        
        self.title("Müşteri Yönetimi")
        self.geometry("800x600")
        
        # Ana frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Müşteri listesi
        self.musteri_listesi = ttk.Treeview(self.main_frame, columns=("ID", "Ad", "Soyad", "Telefon", "E-posta", "Adres"))
        self.musteri_listesi.heading("ID", text="ID")
        self.musteri_listesi.heading("Ad", text="Ad")
        self.musteri_listesi.heading("Soyad", text="Soyad")
        self.musteri_listesi.heading("Telefon", text="Telefon")
        self.musteri_listesi.heading("E-posta", text="E-posta")
        self.musteri_listesi.heading("Adres", text="Adres")
        
        self.musteri_listesi.pack(fill=tk.BOTH, expand=True)
        
        # Butonlar
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.button_frame, text="Yeni Müşteri", command=self.yeni_musteri).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Düzenle", command=self.musteri_duzenle).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Sil", command=self.musteri_sil).pack(side=tk.LEFT, padx=5)
        
        self.musteri_listesini_guncelle()
        
    def musteri_listesini_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.musteri_listesi.get_children():
            self.musteri_listesi.delete(item)
            
        # Veritabanından müşterileri al
        musteriler = self.db.musteri_listesi()
        for musteri in musteriler:
            self.musteri_listesi.insert("", tk.END, values=musteri)
            
    def yeni_musteri(self):
        dialog = MusteriDialog(self)
        self.wait_window(dialog)
        self.musteri_listesini_guncelle()
        
    def musteri_duzenle(self):
        secili = self.musteri_listesi.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen düzenlenecek müşteriyi seçin")
            return
            
        musteri_id = self.musteri_listesi.item(secili[0])["values"][0]
        musteri = self.db.musteri_getir(musteri_id)
        
        dialog = MusteriDialog(self, musteri)
        self.wait_window(dialog)
        self.musteri_listesini_guncelle()
        
    def musteri_sil(self):
        secili = self.musteri_listesi.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silinecek müşteriyi seçin")
            return
            
        if messagebox.askyesno("Onay", "Seçili müşteriyi silmek istediğinizden emin misiniz?"):
            musteri_id = self.musteri_listesi.item(secili[0])["values"][0]
            self.db.musteri_sil(musteri_id)
            self.musteri_listesini_guncelle()

class MusteriDialog(tk.Toplevel):
    def __init__(self, parent, musteri=None):
        super().__init__(parent)
        self.parent = parent
        self.db = VeritabaniYonetici()
        self.musteri = musteri
        
        self.title("Müşteri Bilgileri" if musteri else "Yeni Müşteri")
        self.geometry("400x300")
        
        # Form alanları
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(self.form_frame, text="Ad:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ad_entry = ttk.Entry(self.form_frame)
        self.ad_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.form_frame, text="Soyad:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.soyad_entry = ttk.Entry(self.form_frame)
        self.soyad_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.form_frame, text="Telefon:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.telefon_entry = ttk.Entry(self.form_frame)
        self.telefon_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.form_frame, text="E-posta:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.eposta_entry = ttk.Entry(self.form_frame)
        self.eposta_entry.grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(self.form_frame, text="Adres:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.adres_text = tk.Text(self.form_frame, height=4)
        self.adres_text.grid(row=4, column=1, sticky=tk.EW, pady=5)
        
        # Butonlar
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.button_frame, text="Kaydet", command=self.kaydet).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="İptal", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        if musteri:
            self.form_doldur()
            
    def form_doldur(self):
        self.ad_entry.insert(0, self.musteri["ad"])
        self.soyad_entry.insert(0, self.musteri["soyad"])
        self.telefon_entry.insert(0, self.musteri["telefon"])
        self.eposta_entry.insert(0, self.musteri["eposta"])
        self.adres_text.insert("1.0", self.musteri["adres"])
        
    def kaydet(self):
        veri = {
            "ad": self.ad_entry.get(),
            "soyad": self.soyad_entry.get(),
            "telefon": self.telefon_entry.get(),
            "eposta": self.eposta_entry.get(),
            "adres": self.adres_text.get("1.0", tk.END).strip()
        }
        
        if self.musteri:
            self.db.musteri_guncelle(self.musteri["id"], veri)
        else:
            self.db.musteri_ekle(veri)
            
        self.destroy() 