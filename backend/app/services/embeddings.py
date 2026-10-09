import io
import os
from functools import lru_cache
import numpy as np
from PIL import Image

_models_loaded = False
_clip = None
_text = None

def _norm(v):
    v = np.asarray(v, dtype='float32')
    norm = np.linalg.norm(v)
    if norm < 1e-9:
        return v.tolist()
    return (v / norm).tolist()

@lru_cache(maxsize=1)
def clip_model():
    global _clip
    if os.environ.get('RENDER'):
        return None
    if _clip is None:
        try:
            from sentence_transformers import SentenceTransformer
            _clip = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            print(f"Warning: could not load clip-ViT-B-32: {e}")
            _clip = None
    return _clip

@lru_cache(maxsize=1)
def text_model():
    global _text
    if os.environ.get('RENDER'):
        return None
    if _text is None:
        try:
            from sentence_transformers import SentenceTransformer
            _text = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            print(f"Warning: could not load paraphrase-multilingual-MiniLM-L12-v2: {e}")
            _text = None
    return _text

def _fallback_text_embedding(text: str, dim: int = 384):
    """Deterministic hash/word n-gram embedding fallback when neural model is offline."""
    v = np.zeros(dim, dtype='float32')
    words = (text or '').lower().split()
    if not words:
        v[0] = 1.0
        return v.tolist()
    for i, w in enumerate(words):
        h = hash(w) % dim
        v[h] += 1.0 / (i + 1)**0.5
        # character ngrams
        for j in range(len(w) - 2):
            sub = w[j:j+3]
            v[hash(sub) % dim] += 0.5
    return _norm(v)

def embed_text(text: str):
    m = text_model()
    if m is not None:
        try:
            return _norm(m.encode(text))
        except Exception:
            pass
    return _fallback_text_embedding(text, 384)

def embed_clip_text(text: str):
    m = clip_model()
    if m is not None:
        try:
            return _norm(m.encode(text))
        except Exception:
            pass
    return _fallback_text_embedding(text, 512)

def embed_image(path_or_file):
    m = clip_model()
    if m is not None:
        try:
            if isinstance(path_or_file, (str, bytes, os.PathLike)):
                img = Image.open(path_or_file).convert('RGB')
            else:
                img = Image.open(path_or_file).convert('RGB')
            return _norm(m.encode(img))
        except Exception as e:
            print(f"Image embed error: {e}")
            pass
    # Fallback visual feature extractor from image colors / spatial histogram
    try:
        if isinstance(path_or_file, (str, bytes, os.PathLike)):
            img = Image.open(path_or_file).convert('RGB')
        else:
            img = Image.open(path_or_file).convert('RGB')
        img_thumb = img.resize((16, 16))
        arr = np.array(img_thumb, dtype='float32').flatten()  # 16*16*3 = 768
        if len(arr) >= 512:
            return _norm(arr[:512])
    except Exception:
        pass
    v = np.zeros(512, dtype='float32')
    v[0] = 1.0
    return v.tolist()
