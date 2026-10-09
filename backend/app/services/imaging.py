import io
import os
import uuid
import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image
from ..core.config import settings

ALLOWED = {'image/jpeg', 'image/png', 'image/webp', 'image/jpg'}

# Load OpenCV frontal face cascade
try:
    _cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    _face = cv2.CascadeClassifier(_cascade_path)
except Exception:
    _face = None

def save_image(raw: bytes, content_type: str):
    if content_type not in ALLOWED and not content_type.startswith('image/'):
        raise HTTPException(400, 'Only JPEG, PNG or WebP images are allowed')
    if len(raw) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, 'Image too large (max 10MB)')
    try:
        img = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception:
        raise HTTPException(400, 'Invalid image format')
    
    img.thumbnail((1280, 1280))
    private_dir = os.path.join(settings.UPLOAD_DIR, 'private')
    public_dir = os.path.join(settings.UPLOAD_DIR, 'public')
    os.makedirs(private_dir, exist_ok=True)
    os.makedirs(public_dir, exist_ok=True)
    
    name = uuid.uuid4().hex + '.jpg'
    private_path = os.path.join(private_dir, name)
    # Re-encoding drops EXIF and GPS metadata
    img.save(private_path, 'JPEG', quality=88)
    
    # Process for public copy: detect and blur faces
    arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    if _face is not None:
        try:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            faces = _face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            for (x, y, w, h) in faces:
                # Apply strong Gaussian blur to protect identity
                ksize = (w // 2 * 2 + 1, h // 2 * 2 + 1)
                ksize = (max(21, min(71, ksize[0])), max(21, min(71, ksize[1])))
                arr[y:y + h, x:x + w] = cv2.GaussianBlur(arr[y:y + h, x:x + w], ksize, 0)
        except Exception as e:
            print(f"Face blur notice: {e}")
            
    public_path = os.path.join(public_dir, name)
    cv2.imwrite(public_path, arr)
    return private_path, public_path

def ocr_text(path: str) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(Image.open(path)).strip()[:500]
    except Exception:
        return ''
