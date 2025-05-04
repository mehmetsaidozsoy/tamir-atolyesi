import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime
from database import VeritabaniYonetici

class BackupManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = VeritabaniYonetici()
        
        self.title("Yedekleme Yöneticisi")
        self.geometry("800x450")
        self.resizable(False, False)
        
        # Ana frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Yedekleme ayarları
        self.settings_frame = ttk.LabelFrame(self.main_frame, text="Yedekleme Ayarları")
        self.settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.settings_frame, text="Otomatik Yedekleme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.auto_backup = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.settings_frame, variable=self.auto_backup).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Yedekleme listesi
        self.backup_list = ttk.Treeview(
            self.main_frame,
            columns=("id", "tarih", "dosya_adi", "boyut", "aciklama"),
            show="headings"
        )
        self.backup_list.heading("id", text="ID")
        self.backup_list.heading("tarih", text="Tarih")
        self.backup_list.heading("dosya_adi", text="Dosya Adı")
        self.backup_list.heading("boyut", text="Boyut")
        self.backup_list.heading("aciklama", text="Açıklama")
        self.backup_list.column("id", width=50)
        self.backup_list.column("tarih", width=150)
        self.backup_list.column("dosya_adi", width=220)
        self.backup_list.column("boyut", width=80)
        self.backup_list.column("aciklama", width=200)
        self.backup_list.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.backup_list.yview)
        self.backup_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Butonlar
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.button_frame, text="Yedek Al", command=self.yedekle).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Geri Yükle", command=self.geri_yukle).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Sil", command=self.yedek_sil).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Eksik Yedekleri Temizle", command=self.eksik_yedekleri_temizle).pack(side=tk.LEFT, padx=5)
        
        self.yedek_listesini_guncelle()
        
    def yedek_listesini_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.backup_list.get_children():
            self.backup_list.delete(item)
        # Veritabanındaki yedekleri listele
        yedekler = self.db.tum_yedeklemeler()
        for yedek in yedekler:
            # Tarih formatını düzelt
            try:
                tarih = datetime.strptime(yedek["tarih"], "%Y-%m-%d %H:%M:%S")
                tarih_str = tarih.strftime("%d.%m.%Y %H:%M:%S")
            except Exception:
                tarih_str = yedek["tarih"]
            boyut_kb = int(yedek["boyut"]) // 1024 if yedek["boyut"] else 0
            dosya_yolu = os.path.join("backups", yedek["dosya_adi"])
            exists = os.path.exists(dosya_yolu)
            row_id = self.backup_list.insert(
                "", tk.END,
                values=(yedek["id"], tarih_str, yedek["dosya_adi"], f"{boyut_kb} KB", yedek["aciklama"])
            )
            if not exists:
                self.backup_list.item(row_id, tags=("eksik",))
        self.backup_list.tag_configure("eksik", background="tomato")

    def yedekle(self):
        try:
            self.db.yedek_al("Manuel yedekleme")
            self.db.eski_yedekleri_temizle()
            self.yedek_listesini_guncelle()
            son_yedek = self.db.tum_yedeklemeler()[0]
            messagebox.showinfo("Başarılı", f"Yedekleme tamamlandı.\nTarih: {son_yedek['tarih']}\nDosya: {son_yedek['dosya_adi']}")
        except Exception as e:
            messagebox.showerror("Hata", f"Yedekleme sırasında bir hata oluştu: {str(e)}")

    def geri_yukle(self):
        secili = self.backup_list.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen geri yüklenecek yedeği seçin.")
            return
        yedek_id = self.backup_list.item(secili[0])["values"][0]
        dosya_adi = self.backup_list.item(secili[0])["values"][2]
        dosya_yolu = os.path.join("backups", dosya_adi)
        if not os.path.exists(dosya_yolu):
            messagebox.showerror("Hata", f"Yedek dosyası bulunamadı: {dosya_adi}\nKayıt silinmiş veya taşınmış olabilir.")
            return
        if messagebox.askyesno("Onay", "Seçili yedeği geri yüklemek istediğinizden emin misiniz?\nBu işlem mevcut veritabanını silecektir."):
            try:
                self.db.yedek_geri_yukle(yedek_id)
                self.yedek_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Geri yükleme başarıyla tamamlandı.")
            except Exception as e:
                messagebox.showerror("Hata", f"Geri yükleme sırasında bir hata oluştu: {str(e)}")

    def yedek_sil(self):
        secili = self.backup_list.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silinecek yedeği seçin.")
            return
        if messagebox.askyesno("Onay", "Seçili yedeği silmek istediğinizden emin misiniz?"):
            try:
                yedek_id = self.backup_list.item(secili[0])["values"][0]
                self.db.yedek_sil(yedek_id)
                self.yedek_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Yedek başarıyla silindi.")
            except Exception as e:
                messagebox.showerror("Hata", f"Yedek silme sırasında bir hata oluştu: {str(e)}")

    def eksik_yedekleri_temizle(self):
        sayac = 0
        yedekler = self.db.tum_yedeklemeler()
        for yedek in yedekler:
            dosya_yolu = os.path.join("backups", yedek["dosya_adi"])
            if not os.path.exists(dosya_yolu):
                self.db.yedek_sil(yedek["id"])
                sayac += 1
        self.yedek_listesini_guncelle()
        if sayac > 0:
            messagebox.showinfo("Bilgi", f"{sayac} adet eksik yedek kaydı temizlendi.")
        else:
            messagebox.showinfo("Bilgi", "Eksik yedek kaydı bulunamadı.") 