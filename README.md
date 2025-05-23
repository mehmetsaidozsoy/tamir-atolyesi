# Tamir Atölyesi Yönetim Sistemi

Bu program, tamir atölyelerinin müşteri ve tamir kayıtlarını yönetmek için tasarlanmış bir masaüstü uygulamasıdır.

## İndirme

En son sürümü işletim sisteminize göre aşağıdaki bağlantılardan indirebilirsiniz:

### Windows
- [tamir-atolyesi-1.1.0-windows.zip](https://github.com/mehmetsaidozsoy/tamir-atolyesi/releases/download/untagged-d3b606ebb7937929bc60/tamir-atolyesi-1.0.1-windows.zip))

### Linux
- [tamir-atolyesi-1.1.0-linux.tar.gz](https://github.com/mehmetsaidozsoy/tamir-atolyesi/releases/download/untagged-d3b606ebb7937929bc60/tamir-atolyesi-1.0.1-linux.tar.gz )

## Özellikler

- Müşteri yönetimi (ekleme, düzenleme, silme)
- Tamir kaydı yönetimi (ekleme, düzenleme, silme)
- Maliyet tahmini oluşturma
- PDF ve Excel formatında raporlama
- Otomatik e-posta yedekleme sistemi
- Kullanıcı girişi ve yetkilendirme

## Kurulum

### Windows
1. `TamirAtolyesi-1.1.0-windows.zip` dosyasını indirin
2. ZIP dosyasını açın
3. `setup.exe` dosyasını çalıştırın
4. Kurulum sihirbazını takip edin
5. Program otomatik olarak başlayacaktır

### Linux (Ubuntu/Lubuntu)
1. `tamir-atolyesi-1.1.0-linux.tar.gz` dosyasını indirin
2. Terminal'i açın ve indirilen dosyanın bulunduğu dizine gidin
3. Arşivi açın:
   ```bash
   tar xzf tamir-atolyesi-1.1.0-linux.tar.gz
   cd tamir-atolyesi-1.1.0-linux
   ```
4. Kurulum scriptini çalıştırın:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
5. Kurulum tamamlandıktan sonra programı başlatmak için:
   - Uygulamalar menüsünden "Tamir Atölyesi"ni seçin
   - Veya terminal'den şu komutu çalıştırın:
     ```bash
     tamir_atolyesi
     ```

## Kullanım

1. Program ilk açıldığında kullanıcı girişi yapmanız gerekir
   - Varsayılan kullanıcı adı: admin
   - Varsayılan şifre: 1234

2. Ana ekranda üç sekme bulunur:
   - Müşteriler: Müşteri bilgilerini yönetebilirsiniz
   - Tamirler: Tamir kayıtlarını yönetebilirsiniz
   - Ayarlar: Program ayarlarını yapılandırabilirsiniz

3. E-posta yedekleme için:
   - Ayarlar menüsünden "E-posta Ayarları"nı seçin
   - Gmail hesap bilgilerinizi girin
   - Uygulama şifresini oluşturun ve kaydedin

## Sistem Gereksinimleri

### Windows
- Windows 10 veya üzeri
- 4GB RAM
- 500MB boş disk alanı
- İnternet bağlantısı (e-posta yedekleme için)

### Linux
- Ubuntu 20.04 veya üzeri / Lubuntu 20.04 veya üzeri
- Python 3.8 veya üzeri
- 4GB RAM
- 500MB boş disk alanı
- İnternet bağlantısı (e-posta yedekleme için)

## Destek

Sorun bildirimi ve önerileriniz için:
- GitHub üzerinden "Issues" bölümünü kullanabilirsiniz: https://github.com/mehmetsaidozsoy/tamir-atolyesi/issues
- Veya GitHub profilimden benimle iletişime geçebilirsiniz.

## Lisans

Bu yazılım telif hakkı ile korunmaktadır. © 2025 Tüm hakları saklıdır.
