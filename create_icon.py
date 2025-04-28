from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # İkon boyutları
    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    
    # Ana ikon oluştur (en büyük boyutta)
    size = sizes[-1]
    image = Image.new('RGBA', size, (0,0,0,0))
    draw = ImageDraw.Draw(image)
    
    # Daire çiz
    circle_color = (52, 152, 219)  # Mavi
    margin = size[0] // 8
    draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], fill=circle_color)
    
    # "T" harfi ekle
    text_color = (255, 255, 255)  # Beyaz
    font_size = size[0] // 2
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "T"
    text_bbox = draw.textbbox((0,0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    draw.text((x, y), text, font=font, fill=text_color)
    
    # Farklı boyutlarda kaydet
    images = []
    for size in sizes:
        resized = image.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # ICO dosyası olarak kaydet
    image.save("icon.ico", format="ICO", sizes=sizes)
    print("İkon oluşturuldu: icon.ico")

if __name__ == "__main__":
    create_icon() 