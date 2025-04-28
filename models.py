class Musteri:
    def __init__(self, id=None, ad=None, soyad=None, telefon=None, email=None, adres=None):
        self.id = id
        self.ad = ad
        self.soyad = soyad
        self.telefon = telefon
        self.email = email
        self.adres = adres

    def __str__(self):
        return f"{self.ad} {self.soyad} ({self.telefon})"

class Tamir:
    def __init__(self, id=None, musteri_id=None, cihaz=None, sorun=None, aciklama=None, tarih=None, maliyet=None, durum=None):
        self.id = id
        self.musteri_id = musteri_id
        self.cihaz = cihaz
        self.sorun = sorun
        self.aciklama = aciklama
        self.tarih = tarih
        self.maliyet = maliyet
        self.durum = durum

    def __str__(self):
        return f"{self.cihaz} - {self.sorun}"

class MaliyetTahmini:
    def __init__(self, id=None, tamir_id=None, iscilik_maliyeti=None, malzeme_maliyeti=None, 
                 toplam_maliyet=None, onay_durumu=None, aciklama=None, tarih=None):
        self.id = id
        self.tamir_id = tamir_id
        self.iscilik_maliyeti = iscilik_maliyeti
        self.malzeme_maliyeti = malzeme_maliyeti
        self.toplam_maliyet = toplam_maliyet
        self.onay_durumu = onay_durumu  # 'Beklemede', 'Onaylandı', 'Reddedildi'
        self.aciklama = aciklama
        self.tarih = tarih

    def __str__(self):
        return f"İşçilik: {self.iscilik_maliyeti} TL, Malzeme: {self.malzeme_maliyeti} TL, Toplam: {self.toplam_maliyet} TL" 