# Versiyon numarasını ayarla
$version = "1.0.0"

# Gerekli dizinleri oluştur
New-Item -ItemType Directory -Force -Path "dist"
New-Item -ItemType Directory -Force -Path "build"

Write-Host "Windows paketi oluşturuluyor..."

# PyInstaller ile Windows paketi oluştur
pyinstaller --name="TamirAtolyesi" `
            --onefile `
            --windowed `
            --add-data "DejaVuSans.ttf;." `
            --add-data "config.py;." `
            --add-data "requirements.txt;." `
            "main.py"

Write-Host "Paket oluşturuldu."

# Zip dosyası oluştur
$zipFileName = "TamirAtolyesi-$version-windows.zip"
Compress-Archive -Path "dist\*" -DestinationPath $zipFileName -Force

Write-Host "Release paketi hazır: $zipFileName" 