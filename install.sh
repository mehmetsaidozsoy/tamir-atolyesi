#!/bin/bash

echo "Tamir Atölyesi kurulumu başlatılıyor..."

# Python ve pip'in yüklü olduğunu kontrol et
if ! command -v python3 &> /dev/null; then
    echo "Python3 yüklü değil. Lütfen önce Python3'ü yükleyin."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "pip3 yüklü değil. Lütfen önce pip3'ü yükleyin."
    exit 1
fi

# Gerekli paketleri yükle
echo "Gerekli paketler yükleniyor..."
pip3 install -r requirements.txt

# tkinter'ın yüklü olduğunu kontrol et
python3 -c "import tkinter" 2>/dev/null || {
    echo "tkinter yüklü değil. Yükleniyor..."
    sudo apt-get update
    sudo apt-get install -y python3-tk
}

# Veri dizinlerini oluştur
echo "Veri dizinleri oluşturuluyor..."
mkdir -p ~/.tamir_atolyesi/data
mkdir -p ~/.tamir_atolyesi/logs
mkdir -p ~/.tamir_atolyesi/backups

# Gerekli dosyaları kopyala
echo "Dosyalar kopyalanıyor..."
cp *.py ~/.tamir_atolyesi/
cp DejaVuSans.ttf ~/.tamir_atolyesi/
cp requirements.txt ~/.tamir_atolyesi/

# Çalıştırma script'i oluştur
echo "Çalıştırma script'i oluşturuluyor..."
cat > ~/.local/bin/tamir_atolyesi << 'EOF'
#!/bin/bash
cd ~/.tamir_atolyesi
python3 main.py
EOF

chmod +x ~/.local/bin/tamir_atolyesi

# Desktop dosyası oluştur
echo "Desktop kısayolu oluşturuluyor..."
cat > ~/.local/share/applications/tamir_atolyesi.desktop << EOF
[Desktop Entry]
Name=Tamir Atölyesi
Comment=Tamir Atölyesi Yönetim Sistemi
Exec=tamir_atolyesi
Icon=system-software-install
Terminal=false
Type=Application
Categories=Office;
EOF

echo "Kurulum tamamlandı!"
echo "Programı başlatmak için:"
echo "1. Terminal'den 'tamir_atolyesi' komutunu kullanabilirsiniz"
echo "2. Uygulama menüsünden 'Tamir Atölyesi' simgesine tıklayabilirsiniz" 