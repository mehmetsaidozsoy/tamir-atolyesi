from PIL import Image, ImageDraw

# 32x32 boyutunda yeni bir resim oluştur
img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Test ikonu için basit bir tasarım
draw.rectangle([(4, 4), (28, 28)], outline='#2196F3', width=2)
draw.line([(10, 16), (16, 22), (22, 10)], fill='#2196F3', width=2)

# İkonu kaydet
img.save('icons/test.png') 