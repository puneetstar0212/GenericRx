import os
from PIL import Image, ImageDraw, ImageFont

ICONS_DIR = os.path.dirname(__file__)

def create_pwa_icon(size, filename):
    img = Image.new("RGBA", (size, size), color=(13, 148, 136, 255)) # Teal background
    draw = ImageDraw.Draw(img)
    
    # Draw pill icon shape
    margin = size // 6
    # Outer circle/capsule
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=size // 4, fill=(15, 23, 42, 255), outline=(255, 255, 255, 255), width=size // 30)
    
    # Draw Rx text
    try:
        font = ImageFont.truetype("arial.ttf", size // 3)
    except IOError:
        font = ImageFont.load_default()
        
    text = "Rx"
    draw.text((size // 3, size // 3), text, fill=(45, 212, 191, 255), font=font)
    
    path = os.path.join(ICONS_DIR, filename)
    img.save(path)
    print(f"Generated icon: {path}")

if __name__ == "__main__":
    create_pwa_icon(192, "icon-192.png")
    create_pwa_icon(512, "icon-512.png")
