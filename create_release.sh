#!/bin/bash

VERSION="1.0.0"
PROGRAM="tamir-atolyesi"

# Windows için dist klasörünü yeniden adlandır
mv dist/TamirAtolyesi "dist/${PROGRAM}-${VERSION}-windows"

# Linux için release klasörü oluştur
mkdir -p "dist/${PROGRAM}-${VERSION}-linux"

# Gerekli dosyaları Linux klasörüne kopyala
cp -r \
    main.py \
    gui.py \
    models.py \
    database.py \
    utils.py \
    config.py \
    backup_manager.py \
    requirements.txt \
    README.md \
    DejaVuSans.ttf \
    icon.ico \
    setup.py \
    install.sh \
    debian \
    "dist/${PROGRAM}-${VERSION}-linux/"

# Linux arşivi oluştur
cd dist
tar -czf "${PROGRAM}-${VERSION}-linux.tar.gz" "${PROGRAM}-${VERSION}-linux"
zip -r "${PROGRAM}-${VERSION}-windows.zip" "${PROGRAM}-${VERSION}-windows"

echo "Release paketleri oluşturuldu:"
echo "1. ${PROGRAM}-${VERSION}-linux.tar.gz  (Linux için)"
echo "2. ${PROGRAM}-${VERSION}-windows.zip   (Windows için)" 