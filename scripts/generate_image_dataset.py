"""
Generate synthetic image dataset for Lost & Found items with realistic styling,
brand labels, OCR tokens, and face regions to demonstrate OpenCV blurring.
"""
import os
import random
import math
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter

COLOR_MAP = {
    'black': (35, 35, 38),
    'navy blue': (24, 43, 73),
    'grey': (128, 130, 135),
    'gray': (128, 130, 135),
    'red': (180, 36, 40),
    'green': (38, 115, 60),
    'maroon': (115, 20, 35),
    'blue': (45, 110, 205),
    'white': (240, 240, 245),
    'silver': (195, 200, 208),
    'brown': (120, 75, 45),
    'pink': (235, 120, 160),
    'orange': (235, 115, 35),
    'dark grey': (60, 62, 68),
    'light blue': (100, 170, 240),
}

def get_rgb(color_name):
    c = (color_name or '').lower().strip()
    return COLOR_MAP.get(c, (100, 100, 110))

def draw_face(draw, cx, cy, size=80):
    """Draw a face region that can be recognized by OpenCV Haar Cascade or test blurring."""
    skin = (235, 195, 165)
    hair = (40, 30, 25)
    # Head
    draw.ellipse([cx - size//2, cy - size//2, cx + size//2, cy + size//2], fill=skin, outline=(180, 140, 110), width=2)
    # Hair
    draw.arc([cx - size//2 - 2, cy - size//2 - 4, cx + size//2 + 2, cy + size//4], 180, 360, fill=hair, width=size//5)
    # Eyes
    eye_offset = size // 5
    eye_y = cy - size // 10
    draw.ellipse([cx - eye_offset - 4, eye_y - 3, cx - eye_offset + 4, eye_y + 3], fill=(30, 30, 30))
    draw.ellipse([cx + eye_offset - 4, eye_y - 3, cx + eye_offset + 4, eye_y + 3], fill=(30, 30, 30))
    # Eyebrows
    draw.line([cx - eye_offset - 6, eye_y - 8, cx - eye_offset + 5, eye_y - 7], fill=hair, width=2)
    draw.line([cx + eye_offset - 5, eye_y - 7, cx + eye_offset + 6, eye_y - 8], fill=hair, width=2)
    # Nose
    draw.line([cx, eye_y + 2, cx, eye_y + size // 7], fill=(190, 150, 120), width=2)
    # Mouth
    draw.arc([cx - size // 6, eye_y + size // 8, cx + size // 6, eye_y + size // 4], 0, 180, fill=(180, 80, 80), width=2)

def generate_item_image(cat, brand, color, desc, ocr_tag='', add_face=False, seed=42):
    random.seed(seed)
    w, h = 600, 600
    
    # Background texture / scene
    bg_types = [
        (245, 245, 247), # clean studio table
        (230, 225, 215), # wooden library desk
        (220, 225, 230), # lab workbench
        (240, 242, 238), # campus cafeteria table
    ]
    bg_col = bg_types[seed % len(bg_types)]
    img = Image.new('RGB', (w, h), bg_col)
    draw = ImageDraw.Draw(img)
    
    # Background table perspective lines
    draw.line([(0, 150), (w, 150)], fill=(bg_col[0] - 25, bg_col[1] - 25, bg_col[2] - 25), width=2)
    draw.rectangle([0, 0, w, 150], fill=(bg_col[0] - 15, bg_col[1] - 15, bg_col[2] - 15))
    
    # Drop shadow
    shadow_col = (bg_col[0] - 40, bg_col[1] - 40, bg_col[2] - 40)
    draw.ellipse([140, 430, 460, 520], fill=shadow_col)
    
    item_rgb = get_rgb(color)
    accent_rgb = (max(0, item_rgb[0] - 40), max(0, item_rgb[1] - 40), max(0, item_rgb[2] - 40))
    highlight_rgb = (min(255, item_rgb[0] + 50), min(255, item_rgb[1] + 50), min(255, item_rgb[2] + 50))
    
    # Draw item by category
    cat_lower = (cat or '').lower()
    if 'backpack' in cat_lower or 'bag' in cat_lower:
        # Backpack body
        draw.rounded_rectangle([180, 200, 420, 480], radius=40, fill=item_rgb, outline=accent_rgb, width=4)
        # Front pocket
        draw.rounded_rectangle([200, 310, 400, 450], radius=25, fill=highlight_rgb, outline=accent_rgb, width=3)
        # Zipper lines
        draw.arc([200, 195, 400, 260], 180, 360, fill=(200, 200, 200), width=4)
        draw.line([220, 315, 380, 315], fill=(200, 200, 200), width=3)
        # Straps preview
        draw.line([210, 200, 210, 160], fill=accent_rgb, width=12)
        draw.line([390, 200, 390, 160], fill=accent_rgb, width=12)
        draw.arc([210, 140, 390, 200], 180, 360, fill=accent_rgb, width=12)
    
    elif 'phone' in cat_lower or 'mobile' in cat_lower:
        # Phone chassis
        draw.rounded_rectangle([220, 170, 380, 470], radius=28, fill=item_rgb, outline=(60, 60, 65), width=5)
        # Screen
        draw.rounded_rectangle([230, 185, 370, 455], radius=20, fill=(20, 25, 35))
        # Wallpaper glow
        draw.ellipse([240, 240, 360, 360], fill=(50, 120, 200))
        # Notch / Camera punch
        draw.ellipse([295, 195, 305, 205], fill=(10, 10, 10))
    
    elif 'laptop' in cat_lower:
        # Laptop screen open
        draw.rounded_rectangle([160, 190, 440, 370], radius=15, fill=(40, 42, 48), outline=(160, 165, 175), width=4)
        draw.rectangle([175, 205, 425, 355], fill=(25, 35, 55))
        # Base / Keyboard deck
        draw.polygon([(120, 430), (480, 430), (440, 370), (160, 370)], fill=item_rgb, outline=accent_rgb)
        # Trackpad
        draw.rectangle([260, 395, 340, 425], fill=accent_rgb)
    
    elif 'wallet' in cat_lower or 'purse' in cat_lower:
        # Bifold wallet
        draw.rounded_rectangle([170, 230, 430, 420], radius=20, fill=item_rgb, outline=accent_rgb, width=4)
        draw.line([300, 230, 300, 420], fill=accent_rgb, width=3)
        # Stitching
        for y in range(240, 410, 15):
            draw.line([180, y, 180, y + 8], fill=(220, 220, 190), width=2)
            draw.line([420, y, 420, y + 8], fill=(220, 220, 190), width=2)
        # Card slot preview
        draw.line([190, 280, 280, 280], fill=highlight_rgb, width=3)
    
    elif 'water bottle' in cat_lower or 'bottle' in cat_lower or 'flask' in cat_lower:
        # Bottle cylinder
        draw.rounded_rectangle([250, 230, 350, 470], radius=25, fill=item_rgb, outline=accent_rgb, width=4)
        # Neck & Cap
        draw.rounded_rectangle([270, 180, 330, 230], radius=8, fill=(210, 215, 220), outline=(130, 135, 140), width=3)
        draw.rectangle([280, 160, 320, 180], fill=(60, 60, 65))
        # Volume line
        draw.line([265, 340, 335, 340], fill=highlight_rgb, width=2)
    
    elif 'earbuds' in cat_lower or 'case' in cat_lower:
        # Capsule case
        draw.ellipse([210, 240, 390, 400], fill=item_rgb, outline=accent_rgb, width=4)
        # Split line
        draw.arc([210, 240, 390, 400], 0, 180, fill=accent_rgb, width=3)
        # LED indicator
        draw.ellipse([295, 345, 305, 355], fill=(50, 255, 120))
    
    elif 'keys' in cat_lower:
        # Key ring
        draw.ellipse([260, 200, 340, 280], outline=(200, 205, 215), width=8)
        # 3 keys
        for angle, klen in [(-25, 140), (0, 160), (30, 130)]:
            rad = math.radians(angle)
            x2 = 300 + int(klen * math.sin(rad))
            y2 = 280 + int(klen * math.cos(rad))
            draw.line([(300, 280), (x2, y2)], fill=(180, 185, 195), width=10)
            # Teeth
            draw.line([(x2, y2), (x2 + 8, y2 - 4)], fill=(180, 185, 195), width=6)
    
    elif 'umbrella' in cat_lower:
        # Canopy folded
        draw.polygon([(280, 160), (320, 160), (340, 420), (260, 420)], fill=item_rgb, outline=accent_rgb)
        # Strap
        draw.rectangle([265, 300, 335, 320], fill=accent_rgb)
        # J handle
        draw.arc([270, 420, 330, 480], 0, 180, fill=(50, 35, 25), width=10)
        draw.line([300, 420, 300, 450], fill=(160, 165, 175), width=6)
    
    elif 'calculator' in cat_lower:
        # Calculator casing
        draw.rounded_rectangle([210, 190, 390, 470], radius=18, fill=item_rgb, outline=accent_rgb, width=4)
        # LCD Screen
        draw.rectangle([230, 215, 370, 265], fill=(180, 200, 175), outline=(100, 110, 95), width=2)
        # Solar strip
        draw.rectangle([250, 275, 350, 290], fill=(60, 45, 55))
        # Keys matrix
        for row in range(5):
            for col in range(4):
                kx = 230 + col * 36
                ky = 305 + row * 30
                draw.rounded_rectangle([kx, ky, kx + 28, ky + 22], radius=4, fill=(55, 60, 68), outline=(40, 45, 50))
    
    else:
        # Generic object
        draw.rounded_rectangle([200, 220, 400, 440], radius=25, fill=item_rgb, outline=accent_rgb, width=4)

    # Brand badge or text
    if brand and brand.strip():
        btext = brand.strip().upper()
        draw.rectangle([250, 485, 350, 510], fill=(255, 255, 255), outline=(200, 200, 200))
        draw.text((260, 490), btext[:12], fill=(40, 40, 40))

    # OCR text label or tag
    if ocr_tag and ocr_tag.strip():
        tag_text = ocr_tag.strip().upper()
        draw.rectangle([340, 210, 450, 245], fill=(255, 250, 200), outline=(180, 160, 50), width=2)
        draw.text((345, 220), tag_text[:14], fill=(20, 20, 20))

    # Add face if requested (e.g. for demonstrating Haar cascade face blur on public upload)
    if add_face:
        draw_face(draw, 100, 100, size=90)

    return img

def create_dataset_images(max_images=120):
    os.makedirs('data/images', exist_ok=True)
    os.makedirs('uploads/private', exist_ok=True)
    os.makedirs('uploads/public', exist_ok=True)
    
    lost_df = pd.read_csv('data/lost_found_dataset/lost_reports.csv')
    found_df = pd.read_csv('data/lost_found_dataset/found_reports.csv')
    
    count = 0
    # Process reports that have has_image=True or sample some
    for idx, row in found_df.head(max_images // 2).iterrows():
        rid = row['report_id']
        cat = str(row['category_reported'])
        desc = str(row['description'])
        
        # Extract color and brand hints
        colors = ['navy blue', 'black', 'grey', 'gray', 'red', 'green', 'maroon', 'blue', 'white', 'silver', 'brown', 'pink', 'orange']
        col = next((c for c in colors if c in desc.lower()), 'blue')
        brand_guess = ''
        for b in ['Nike', 'Adidas', 'Puma', 'Wildcraft', 'Apple', 'Samsung', 'Dell', 'HP', 'boAt', 'Casio', 'Milton', 'Fastrack']:
            if b.lower() in desc.lower():
                brand_guess = b
                break
        
        ocr_hint = f"LF-{rid}" if random.random() < 0.4 else ""
        add_face = (idx % 8 == 0) # Every 8th image has a face in background
        
        img = generate_item_image(cat, brand_guess, col, desc, ocr_tag=ocr_hint, add_face=add_face, seed=idx*7 + 13)
        filename = f"{rid.lower()}_item.jpg"
        save_path = os.path.join('data/images', filename)
        img.save(save_path, 'JPEG', quality=90)
        found_df.at[idx, 'image_file'] = filename
        found_df.at[idx, 'has_image'] = True
        count += 1

    for idx, row in lost_df.head(max_images // 2).iterrows():
        rid = row['report_id']
        cat = str(row['category_reported'])
        desc = str(row['description'])
        colors = ['navy blue', 'black', 'grey', 'gray', 'red', 'green', 'maroon', 'blue', 'white', 'silver', 'brown', 'pink', 'orange']
        col = next((c for c in colors if c in desc.lower()), 'black')
        brand_guess = ''
        for b in ['Nike', 'Adidas', 'Puma', 'Wildcraft', 'Apple', 'Samsung', 'Dell', 'HP', 'boAt', 'Casio', 'Milton', 'Fastrack']:
            if b.lower() in desc.lower():
                brand_guess = b
                break
        
        ocr_hint = f"ROOM {100 + idx}" if random.random() < 0.3 else ""
        add_face = (idx % 10 == 0)
        img = generate_item_image(cat, brand_guess, col, desc, ocr_tag=ocr_hint, add_face=add_face, seed=idx*11 + 42)
        filename = f"{rid.lower()}_item.jpg"
        save_path = os.path.join('data/images', filename)
        img.save(save_path, 'JPEG', quality=90)
        lost_df.at[idx, 'image_file'] = filename
        lost_df.at[idx, 'has_image'] = True
        count += 1

    found_df.to_csv('data/lost_found_dataset/found_reports.csv', index=False)
    lost_df.to_csv('data/lost_found_dataset/lost_reports.csv', index=False)
    print(f"Generated {count} synthetic item images saved to data/images/ and updated CSVs.")

if __name__ == '__main__':
    create_dataset_images()
