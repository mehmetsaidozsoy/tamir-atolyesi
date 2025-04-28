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

logger = logging.getLogger(__name__)

class TamirAtolyesiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tamir Atölyesi Yönetim Sistemi")
        self.root.geometry("1000x700")
        
        # Kullanıcı girişi kontrolü
        if not self.kullanici_girisi():
            self.root.destroy()
            return
        
        # Menü çubuğu oluştur
        self.menu_olustur()
        
        # Ana pencere için grid yapılandırması
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Veritabanı bağlantısı
        self.db = VeritabaniYonetici()
        self.conn = self.db.conn
        self.cursor = self.db.cursor
        
        # Yedekleme yöneticisi
        self.yedek_yoneticisi = YedekYoneticisi()
        
        # Notebook (Sekmeler) oluştur
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Müşteri sekmesi
        self.musteri_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.musteri_frame, text="Müşteriler")
        
        # Tamir sekmesi
        self.tamir_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tamir_frame, text="Tamirler")
        
        # Ayarlar sekmesi
        self.ayarlar_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.ayarlar_frame, text="Ayarlar")
        
        # Müşteri sekmesi içeriği
        self.musteri_sekmesi_olustur()
        
        # Tamir sekmesi içeriği
        self.tamir_sekmesi_olustur()
        
        # Ayarlar sekmesi içeriği
        self.ayarlar_sekmesi_olustur()
        
        # Otomatik yedeklemeyi başlat
        self.yedek_yoneticisi.start_scheduler()
        
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
    
    def kullanici_girisi(self):
        """Kullanıcı girişi penceresini gösterir"""
        dialog = KullaniciGirisDialog(self.root)
        return dialog.result
    
    def kullanici_ayarlari_goster(self):
        """Kullanıcı ayarları penceresini gösterir"""
        KullaniciAyarlariDialog(self.root)
    
    def hakkinda_goster(self):
        """Hakkında penceresini gösterir"""
        messagebox.showinfo(
            "Hakkında",
            "Tamir Atölyesi Yönetim Sistemi\n\n"
            "Sürüm: 1.0.0\n"
            "© 2024 Tüm hakları saklıdır.\n\n"
            "Bu program tamir atölyelerinin müşteri ve tamir kayıtlarını\n"
            "yönetmek için tasarlanmıştır."
        )
    
    def musteri_sekmesi_olustur(self):
        # Müşteri sekmesi için grid yapılandırması
        self.musteri_frame.grid_rowconfigure(1, weight=1)
        self.musteri_frame.grid_columnconfigure(0, weight=1)
        
        # Başlık
        ttk.Label(self.musteri_frame, text="Müşteri Yönetimi", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Arama çerçevesi
        self.musteri_arama_frame = ttk.LabelFrame(self.musteri_frame, text="Müşteri Arama", padding="10")
        self.musteri_arama_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.musteri_arama_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(self.musteri_arama_frame, text="Ara:").grid(row=0, column=0, padx=5)
        self.musteri_arama_entry = ttk.Entry(self.musteri_arama_frame)
        self.musteri_arama_entry.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(self.musteri_arama_frame, text="Ara", command=self.musteri_ara).grid(row=0, column=2, padx=5)
        
        # Müşteri listesi
        self.musteri_liste_frame = ttk.LabelFrame(self.musteri_frame, text="Müşteri Listesi", padding="10")
        self.musteri_liste_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)
        self.musteri_liste_frame.grid_rowconfigure(0, weight=1)
        self.musteri_liste_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollbar
        self.musteri_scrollbar = ttk.Scrollbar(self.musteri_liste_frame)
        self.musteri_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.musteri_listesi = ttk.Treeview(self.musteri_liste_frame, 
                                          columns=("ID", "Ad", "Soyad", "Telefon", "Email", "Adres"), 
                                          show="headings",
                                          yscrollcommand=self.musteri_scrollbar.set)
        self.musteri_listesi.grid(row=0, column=0, sticky="nsew")
        self.musteri_scrollbar.config(command=self.musteri_listesi.yview)
        
        # Sütun başlıkları ve genişlikleri
        self.musteri_listesi.heading("ID", text="ID")
        self.musteri_listesi.heading("Ad", text="Ad")
        self.musteri_listesi.heading("Soyad", text="Soyad")
        self.musteri_listesi.heading("Telefon", text="Telefon")
        self.musteri_listesi.heading("Email", text="Email")
        self.musteri_listesi.heading("Adres", text="Adres")
        
        self.musteri_listesi.column("ID", width=50, anchor="center")
        self.musteri_listesi.column("Ad", width=100, anchor="w")
        self.musteri_listesi.column("Soyad", width=100, anchor="w")
        self.musteri_listesi.column("Telefon", width=120, anchor="w")
        self.musteri_listesi.column("Email", width=200, anchor="w")
        self.musteri_listesi.column("Adres", width=300, anchor="w")
        
        # Butonlar
        self.musteri_buton_frame = ttk.Frame(self.musteri_frame, padding="10")
        self.musteri_buton_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.musteri_buton_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        ttk.Button(self.musteri_buton_frame, text="Yeni Müşteri", command=self.yeni_musteri).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(self.musteri_buton_frame, text="Müşteri Düzenle", command=self.musteri_duzenle).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(self.musteri_buton_frame, text="Müşteri Sil", command=self.musteri_sil).grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Button(self.musteri_buton_frame, text="Tamir Ekle", command=self.tamir_ekle).grid(row=0, column=3, padx=5, sticky="ew")
        ttk.Button(self.musteri_buton_frame, text="Rapor", command=self.rapor_goster).grid(row=0, column=4, padx=5, sticky="ew")
        
        # Müşteri listesini güncelle
        self.musteri_listesini_guncelle()
        
    def tamir_sekmesi_olustur(self):
        # Tamir sekmesi için grid yapılandırması
        self.tamir_frame.grid_rowconfigure(1, weight=1)
        self.tamir_frame.grid_columnconfigure(0, weight=1)
        
        # Başlık
        ttk.Label(self.tamir_frame, text="Tamir Yönetimi", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Arama çerçevesi
        self.tamir_arama_frame = ttk.LabelFrame(self.tamir_frame, text="Tamir Arama", padding="10")
        self.tamir_arama_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.tamir_arama_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(self.tamir_arama_frame, text="Ara:").grid(row=0, column=0, padx=5)
        self.tamir_arama_entry = ttk.Entry(self.tamir_arama_frame)
        self.tamir_arama_entry.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(self.tamir_arama_frame, text="Ara", command=self.tamir_ara).grid(row=0, column=2, padx=5)
        
        # Tamir listesi
        self.tamir_liste_frame = ttk.LabelFrame(self.tamir_frame, text="Tamir Listesi", padding="10")
        self.tamir_liste_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)
        self.tamir_liste_frame.grid_rowconfigure(0, weight=1)
        self.tamir_liste_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollbar
        self.tamir_scrollbar = ttk.Scrollbar(self.tamir_liste_frame)
        self.tamir_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.tamir_listesi = ttk.Treeview(self.tamir_liste_frame, 
                                        columns=("ID", "Müşteri", "Cihaz", "Sorun", "Tarih", "Maliyet", "Durum"), 
                                        show="headings",
                                        yscrollcommand=self.tamir_scrollbar.set)
        self.tamir_listesi.grid(row=0, column=0, sticky="nsew")
        self.tamir_scrollbar.config(command=self.tamir_listesi.yview)
        
        # Sütun başlıkları ve genişlikleri
        self.tamir_listesi.heading("ID", text="ID")
        self.tamir_listesi.heading("Müşteri", text="Müşteri")
        self.tamir_listesi.heading("Cihaz", text="Cihaz")
        self.tamir_listesi.heading("Sorun", text="Sorun")
        self.tamir_listesi.heading("Tarih", text="Tarih")
        self.tamir_listesi.heading("Maliyet", text="Maliyet")
        self.tamir_listesi.heading("Durum", text="Durum")
        
        self.tamir_listesi.column("ID", width=50, anchor="center")
        self.tamir_listesi.column("Müşteri", width=150, anchor="w")
        self.tamir_listesi.column("Cihaz", width=100, anchor="w")
        self.tamir_listesi.column("Sorun", width=200, anchor="w")
        self.tamir_listesi.column("Tarih", width=100, anchor="center")
        self.tamir_listesi.column("Maliyet", width=100, anchor="e")
        self.tamir_listesi.column("Durum", width=100, anchor="center")
        
        # Butonlar
        self.tamir_buton_frame = ttk.Frame(self.tamir_frame, padding="10")
        self.tamir_buton_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.tamir_buton_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        ttk.Button(self.tamir_buton_frame, text="Yeni Tamir", command=self.yeni_tamir).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(self.tamir_buton_frame, text="Tamir Düzenle", command=self.tamir_duzenle).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(self.tamir_buton_frame, text="Tamir Sil", command=self.tamir_sil).grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Button(self.tamir_buton_frame, text="Maliyet Tahmini", command=self.maliyet_tahmini).grid(row=0, column=3, padx=5, sticky="ew")
        ttk.Button(self.tamir_buton_frame, text="Rapor", command=self.rapor_goster).grid(row=0, column=4, padx=5, sticky="ew")
        
        # Tamir listesini güncelle
        self.tamir_listesini_guncelle()
    
    def musteri_listesini_guncelle(self):
        """Müşteri listesini günceller"""
        try:
            # Mevcut listeyi temizle
            for item in self.musteri_listesi.get_children():
                self.musteri_listesi.delete(item)
            
            # Veritabanından müşterileri al
            musteriler = self.db.musteri_ara("")
            
            # Müşterileri listeye ekle
            for musteri in musteriler:
                self.musteri_listesi.insert("", "end", values=(
                    musteri.id,
                    musteri.ad,
                    musteri.soyad,
                    musteri.telefon,
                    musteri.email or "",
                    musteri.adres or ""
                ))
        except Exception as e:
            logger.error(f"Müşteri listesi güncelleme hatası: {str(e)}")
            messagebox.showerror("Hata", "Müşteri listesi güncellenirken bir hata oluştu.")
    
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
        """Ayarlar sekmesi içeriğini oluşturur"""
        # Başlık
        ttk.Label(self.ayarlar_frame, text="Yedekleme ve Ayarlar", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # E-posta ayarları butonu
        ttk.Button(self.ayarlar_frame, text="E-posta Ayarları", 
                  command=self.email_ayarlari_goster).grid(row=1, column=0, pady=10, padx=5)
        
        # Manuel yedekleme butonu
        ttk.Button(self.ayarlar_frame, text="Manuel Yedek Al ve Gönder", 
                  command=self.manuel_yedek_al).grid(row=1, column=1, pady=10, padx=5)
        
        # Mevcut ayarları göster
        ayarlar_frame = ttk.LabelFrame(self.ayarlar_frame, text="Mevcut Ayarlar", padding="10")
        ayarlar_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10, padx=5)
        
        ttk.Label(ayarlar_frame, text=f"Gönderen E-posta: {EMAIL_CONFIG['sender_email']}").pack(anchor="w")
        ttk.Label(ayarlar_frame, text=f"Alıcı E-posta: {EMAIL_CONFIG['receiver_email']}").pack(anchor="w")
        ttk.Label(ayarlar_frame, text=f"Otomatik Yedekleme Saati: {EMAIL_CONFIG['backup_time']}").pack(anchor="w")
    
    def email_ayarlari_goster(self):
        """E-posta ayarları penceresini açar"""
        EmailAyarlariDialog(self.root)
        # Ayarlar sekmesini güncelle
        self.ayarlar_sekmesi_olustur()
    
    def manuel_yedek_al(self):
        """Manuel olarak yedek alır ve e-posta ile gönderir"""
        if self.yedek_yoneticisi.yedegi_gonder():
            messagebox.showinfo("Başarılı", "Yedek başarıyla alındı ve e-posta ile gönderildi.")
        else:
            messagebox.showerror("Hata", "Yedek alma veya gönderme sırasında bir hata oluştu.")

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
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Grid yapılandırması
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Tarih seçimi (takvimli)
        ttk.Label(self, text="Başlangıç Tarihi:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.baslangic_tarihi = DateEntry(self, date_pattern="yyyy-mm-dd", locale="tr_TR")
        self.baslangic_tarihi.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="Bitiş Tarihi:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.bitis_tarihi = DateEntry(self, date_pattern="yyyy-mm-dd", locale="tr_TR")
        self.bitis_tarihi.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Rapor formatı seçimi
        ttk.Label(self, text="Rapor Formatı:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.rapor_format = ttk.Combobox(self, values=["PDF", "Excel"], state="readonly")
        self.rapor_format.set("PDF")
        self.rapor_format.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Butonlar
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Rapor Oluştur", command=self.rapor_olustur).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def rapor_olustur(self):
        baslangic = self.baslangic_tarihi.get()
        bitis = self.bitis_tarihi.get()
        format = self.rapor_format.get()
        
        if not baslangic or not bitis:
            messagebox.showerror("Hata", "Lütfen tarih aralığını belirtin")
            return
        
        try:
            if format == "PDF":
                self.pdf_raporu_olustur(baslangic, bitis)
            else:
                self.excel_raporu_olustur(baslangic, bitis)
            messagebox.showinfo("Başarılı", "Rapor başarıyla oluşturuldu")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken bir hata oluştu: {str(e)}")
    
    def pdf_raporu_olustur(self, baslangic, bitis):
        import os
        from pathlib import Path
        from datetime import datetime
        from models import Musteri, Tamir
        
        belgeler_klasoru = str(Path.home() / "Documents")
        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        dosya_adi = f"tamir_raporu_{zaman_damgasi}.pdf"
        dosya_yolu = os.path.join(belgeler_klasoru, dosya_adi)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, "Tamir Atölyesi Raporu", ln=True, align="C")
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, f"Tarih Aralığı: {baslangic} - {bitis}", ln=True)
        pdf.cell(0, 10, f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", ln=True)
        pdf.ln(10)
        
        musteri_tamirler = self.db.musteri_tamir_raporu(baslangic, bitis)
        for row in musteri_tamirler:
            musteri = Musteri(id=row[0], ad=row[1], soyad=row[2], telefon=row[3], email=row[4], adres=row[5])
            tamir = Tamir(id=row[6], musteri_id=row[7], cihaz=row[8], sorun=row[9], tarih=row[10], maliyet=row[11], durum=row[12])
            pdf.set_font('DejaVu', '', 12)
            pdf.cell(0, 10, f"Müşteri: {musteri.ad} {musteri.soyad}", ln=True)
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 10, f"Telefon: {musteri.telefon}", ln=True)
            pdf.cell(0, 10, f"Tamir Açıklaması: {tamir.sorun}", ln=True)
            pdf.cell(0, 10, f"Tamir Tarihi: {tamir.tarih}", ln=True)
            pdf.cell(0, 10, f"Durum: {tamir.durum}", ln=True)
            pdf.ln(5)
        try:
            pdf.output(dosya_yolu)
            messagebox.showinfo("Başarılı", f"Rapor başarıyla oluşturuldu:\n{dosya_yolu}")
        except Exception as e:
            print(f"PDF raporu oluşturma hatası: {e}")
            messagebox.showerror("Hata", "PDF raporu oluşturulurken bir hata oluştu.")
    
    def excel_raporu_olustur(self, baslangic, bitis):
        from datetime import datetime
        from models import Musteri, Tamir
        belgeler_klasoru = str(Path.home() / "Documents")
        zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
        dosya_adi = f"tamir_raporu_{zaman_damgasi}.xlsx"
        dosya_yolu = os.path.join(belgeler_klasoru, dosya_adi)
        musteri_tamirler = self.db.musteri_tamir_raporu(baslangic, bitis)
        data = []
        for row in musteri_tamirler:
            musteri = Musteri(id=row[0], ad=row[1], soyad=row[2], telefon=row[3], email=row[4], adres=row[5])
            tamir = Tamir(id=row[6], musteri_id=row[7], cihaz=row[8], sorun=row[9], tarih=row[10], maliyet=row[11], durum=row[12])
            data.append({
                "Müşteri Adı": musteri.ad,
                "Müşteri Soyadı": musteri.soyad,
                "Telefon": musteri.telefon,
                "Tamir Açıklaması": tamir.sorun,
                "Tamir Tarihi": tamir.tarih,
                "Durum": tamir.durum
            })
        df = pd.DataFrame(data)
        try:
            with pd.ExcelWriter(dosya_yolu, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Tamir Raporu')
                rapor_bilgileri = pd.DataFrame({
                    'Rapor Bilgileri': [
                        f'Tarih Aralığı: {baslangic} - {bitis}',
                        f'Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}',
                        f'Toplam Kayıt: {len(data)}'
                    ]
                })
                rapor_bilgileri.to_excel(writer, index=False, sheet_name='Rapor Bilgileri')
            messagebox.showinfo("Başarılı", f"Rapor başarıyla oluşturuldu:\n{dosya_yolu}")
        except Exception as e:
            print(f"Excel raporu oluşturma hatası: {e}")
            messagebox.showerror("Hata", "Excel raporu oluşturulurken bir hata oluştu.")

class EmailAyarlariDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("E-posta Yedekleme Ayarları")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Dialog için grid yapılandırması
        self.dialog.grid_rowconfigure(6, weight=1)
        self.dialog.grid_columnconfigure(1, weight=1)
        
        # E-posta ayarları
        ttk.Label(self.dialog, text="Gönderen E-posta:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.sender_email = ttk.Entry(self.dialog, width=40)
        self.sender_email.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.sender_email.insert(0, EMAIL_CONFIG["sender_email"])
        
        ttk.Label(self.dialog, text="Uygulama Şifresi:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.sender_password = ttk.Entry(self.dialog, width=40, show="*")
        self.sender_password.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.sender_password.insert(0, EMAIL_CONFIG["sender_password"])
        
        ttk.Label(self.dialog, text="Alıcı E-posta:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.receiver_email = ttk.Entry(self.dialog, width=40)
        self.receiver_email.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.receiver_email.insert(0, EMAIL_CONFIG["receiver_email"])
        
        ttk.Label(self.dialog, text="Yedekleme Saati:", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.backup_time = ttk.Entry(self.dialog, width=40)
        self.backup_time.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.backup_time.insert(0, EMAIL_CONFIG["backup_time"])
        
        # Bilgi etiketi
        info_text = "Not: Gmail için 'Uygulama Şifresi' kullanmanız gerekir.\n" + \
                   "Bunun için Google Hesap ayarlarından 2 adımlı doğrulamayı açıp\n" + \
                   "uygulama şifresi oluşturmalısınız."
        info_label = ttk.Label(self.dialog, text=info_text, font=("Arial", 9), foreground="gray")
        info_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        
        # Butonlar
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        button_frame.grid_columnconfigure((0,1,2), weight=1)
        
        ttk.Button(button_frame, text="Bağlantıyı Test Et", command=self.test_connection).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Kaydet", command=self.kaydet).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="İptal", command=self.dialog.destroy).grid(row=0, column=2, padx=5)
        
        self.dialog.wait_window()
    
    def test_connection(self):
        """E-posta bağlantısını test eder"""
        yedek_yoneticisi = YedekYoneticisi()
        yedek_yoneticisi.email_ayarlarini_guncelle(
            self.sender_email.get(),
            self.sender_password.get(),
            self.receiver_email.get(),
            self.backup_time.get()
        )
        if yedek_yoneticisi.test_email_connection():
            messagebox.showinfo("Başarılı", "E-posta bağlantısı başarılı!")
        else:
            messagebox.showerror("Hata", "E-posta bağlantısı başarısız!")
    
    def kaydet(self):
        """E-posta ayarlarını kaydeder"""
        yedek_yoneticisi = YedekYoneticisi()
        yedek_yoneticisi.email_ayarlarini_guncelle(
            self.sender_email.get(),
            self.sender_password.get(),
            self.receiver_email.get(),
            self.backup_time.get()
        )
        messagebox.showinfo("Başarılı", "E-posta ayarları kaydedildi!")
        self.dialog.destroy()

class KullaniciGirisDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Kullanıcı Girişi")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Dialog'u ekranın ortasına konumlandır
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')
        
        self.result = False
        
        # Form alanları
        ttk.Label(self.dialog, text="Kullanıcı Adı:").grid(row=0, column=0, padx=10, pady=10)
        self.kullanici_adi = ttk.Entry(self.dialog)
        self.kullanici_adi.grid(row=0, column=1, padx=10, pady=10)
        self.kullanici_adi.focus()
        
        ttk.Label(self.dialog, text="Şifre:").grid(row=1, column=0, padx=10, pady=10)
        self.sifre = ttk.Entry(self.dialog, show="*")
        self.sifre.grid(row=1, column=1, padx=10, pady=10)
        
        # Butonlar
        ttk.Button(self.dialog, text="Giriş", command=self.giris_yap).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Enter tuşu ile giriş yapma
        self.dialog.bind('<Return>', lambda e: self.giris_yap())
        
        self.dialog.wait_window()
    
    def giris_yap(self):
        """Kullanıcı girişini kontrol eder"""
        kullanici_adi = self.kullanici_adi.get()
        sifre = self.sifre.get()
        
        # TODO: Gerçek kullanıcı doğrulama sistemi eklenecek
        # Şimdilik basit bir kontrol
        if kullanici_adi == "admin" and sifre == "1234":
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı!")

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