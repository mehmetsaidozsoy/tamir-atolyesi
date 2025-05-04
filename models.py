from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Musteri:
    id: Optional[int] = None
    tc_no: str = ""
    ad: str = ""
    soyad: str = ""
    telefon: str = ""
    email: Optional[str] = None
    adres: Optional[str] = None
    kayit_tarihi: datetime = datetime.now()

    def __str__(self):
        return f"{self.ad} {self.soyad} ({self.telefon})"

@dataclass
class Arac:
    id: Optional[int] = None
    musteri_id: int = 0
    plaka: str = ""
    marka: str = ""
    model: str = ""
    yil: int = 0
    renk: Optional[str] = None
    sasi_no: Optional[str] = None

@dataclass
class Onarim:
    id: Optional[int] = None
    arac_id: int = 0
    giris_tarihi: datetime = datetime.now()
    cikis_tarihi: Optional[datetime] = None
    sorun: str = ""
    yapilan_islem: Optional[str] = None
    parcalar: Optional[str] = None
    iscilik_ucreti: float = 0.0
    parca_ucreti: float = 0.0
    toplam_ucret: float = 0.0
    durum: str = "Beklemede"

@dataclass
class Kullanici:
    id: Optional[int] = None
    kullanici_adi: str = ""
    sifre_hash: str = ""
    yetki_seviyesi: int = 1

@dataclass
class Ayar:
    id: Optional[int] = None
    anahtar: str = ""
    deger: str = ""

class Tamir:
    def __init__(self, id=None, musteri_id=None, cihaz=None, marka=None, model=None, 
                 ariza=None, durum=None, notlar=None, baslama_tarihi=None, 
                 bitis_tarihi=None, ucret=None):
        self.id = id
        self.musteri_id = musteri_id
        self.cihaz = cihaz
        self.marka = marka
        self.model = model
        self.ariza = ariza
        self.durum = durum
        self.notlar = notlar
        self.baslama_tarihi = baslama_tarihi
        self.bitis_tarihi = bitis_tarihi
        self.ucret = ucret

    def __str__(self):
        return f"{self.cihaz} - {self.ariza}"

class MaliyetTahmini:
    def __init__(self, id=None, tamir_id=None, parca_maliyeti=None, 
                 iscilik_maliyeti=None, ek_maliyetler=None, toplam_maliyet=None):
        self.id = id
        self.tamir_id = tamir_id
        self.parca_maliyeti = parca_maliyeti
        self.iscilik_maliyeti = iscilik_maliyeti
        self.ek_maliyetler = ek_maliyetler
        self.toplam_maliyet = toplam_maliyet

    def __str__(self):
        return f"İşçilik: {self.iscilik_maliyeti} TL, Malzeme: {self.parca_maliyeti} TL, Toplam: {self.toplam_maliyet} TL" 