import math
import os
import re
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models import Match, Report, has_pgvector

WEIGHTS = {
    'text': 0.30,
    'image': 0.25,
    'color': 0.08,
    'brand': 0.07,
    'geo': 0.15,
    'time': 0.10,
    'ocr': 0.05,
}

CROSS_MODAL_SCALE = 3.0

COLOR_FAMILY = {
    'black': 'dark', 'grey': 'dark', 'gray': 'dark', 'navy blue': 'blue', 'blue': 'blue',
    'red': 'red', 'maroon': 'red', 'green': 'green', 'white': 'light',
    'silver': 'light', 'brown': 'brown', 'pink': 'red', 'orange': 'orange',
}

FEATURES = ['text', 'image', 'color', 'brand', 'geo', 'time', 'ocr']

def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000.0 * math.asin(math.sqrt(max(0.0, min(1.0, a))))

def cosine(a, b):
    if a is None or b is None:
        return None
    va, vb = np.asarray(a, dtype='float32'), np.asarray(b, dtype='float32')
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))

def color_score(a, b):
    if not a or not b:
        return None
    ca, cb = a.strip().lower(), b.strip().lower()
    if ca == cb:
        return 1.0
    return 0.5 if ca in COLOR_FAMILY and COLOR_FAMILY.get(ca) == COLOR_FAMILY.get(cb) else 0.0

def brand_score(a, b):
    if not a or not b:
        return 0.5  # unknown is neutral
    return 1.0 if a.strip().lower() == b.strip().lower() else 0.0

def tokens(s):
    return set(re.findall(r'[a-z0-9]{3,}', (s or '').lower()))

def ocr_score(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return None
    union = ta | tb
    return len(ta & tb) / len(union) if union else 0.0

def pair_components(lost, found):
    # Location distance
    lat1 = getattr(lost.place, 'latitude', 12.9) if hasattr(lost, 'place') and lost.place else 12.9
    lon1 = getattr(lost.place, 'longitude', 77.5) if hasattr(lost, 'place') and lost.place else 77.5
    lat2 = getattr(found.place, 'latitude', 12.9) if hasattr(found, 'place') and found.place else 12.9
    lon2 = getattr(found.place, 'longitude', 77.5) if hasattr(found, 'place') and found.place else 77.5
    
    d = haversine_m(lat1, lon1, lat2, lon2)
    
    # Time window score
    hours = (found.event_time - lost.event_time).total_seconds() / 3600.0
    earliest = -(lost.time_window_hours / 2.0 + 2.0)
    time_s = 0.0 if hours < earliest else math.exp(-max(hours, 0.0) / 30.0)
    
    comp = {
        'text': cosine(lost.txt_emb, found.txt_emb),
        'image': cosine(lost.img_emb, found.img_emb),
        'color': color_score(lost.color, found.color),
        'brand': brand_score(lost.brand, found.brand),
        'geo': math.exp(-d / 250.0),
        'time': time_s,
        'ocr': ocr_score(lost.ocr_text, found.ocr_text),
    }
    
    # Cross-modal CLIP text-to-image fallback if only one side has a photo
    if comp['image'] is None:
        if lost.img_emb is None and found.img_emb is not None:
            c = cosine(lost.clip_txt_emb, found.img_emb)
        elif found.img_emb is None and lost.img_emb is not None:
            c = cosine(found.clip_txt_emb, lost.img_emb)
        else:
            c = None
        comp['image'] = None if c is None else min(1.0, max(0.0, c * CROSS_MODAL_SCALE))
        
    return comp

def weighted_score(comp):
    num = den = 0.0
    for k, w in WEIGHTS.items():
        v = comp.get(k)
        if v is None:
            continue
        num += w * max(0.0, min(1.0, v))
        den += w
    return num / den if den else 0.0

RANKER = None

def load_ranker(path):
    try:
        import lightgbm as lgb
        booster = lgb.Booster(model_file=path)
        def predict(comp):
            x = [[-1.0 if comp.get(k) is None else comp[k] for k in FEATURES]]
            pred = booster.predict(x)[0]
            return 1.0 / (1.0 + math.exp(-pred))
        return predict
    except Exception as e:
        print(f"Could not load LightGBM ranker from {path}: {e}")
        return None

def score_pair(comp):
    if RANKER is not None:
        return float(RANKER(comp))
    return weighted_score(comp)

def confidence(score):
    return 'high' if score >= 0.75 else 'medium' if score >= 0.55 else 'low'

def candidates(db: Session, rep: Report, k: int = 50):
    opposite = 'found' if rep.type == 'lost' else 'lost'
    q = select(Report).where(
        Report.type == opposite,
        Report.status == 'open',
        Report.user_id != rep.user_id
    )
    if rep.group != 'other':
        q = q.where(Report.group.in_([rep.group, 'other']))
        
    # If postgres with pgvector
    if has_pgvector and rep.txt_emb is not None:
        q = q.order_by(Report.txt_emb.cosine_distance(rep.txt_emb))
        return db.scalars(q.limit(k)).all()
        
    # Otherwise retrieve open matches and rank candidates by vector distance in Python
    pool = db.scalars(q.limit(200)).all()
    if rep.txt_emb is not None:
        pool.sort(key=lambda r: -(cosine(rep.txt_emb, r.txt_emb) or 0.0))
    return pool[:k]

def run_matching(db: Session, report_id: int):
    rep = db.get(Report, report_id)
    if not rep or rep.status != 'open':
        return []
    
    scored = []
    for other in candidates(db, rep):
        lost, found = (rep, other) if rep.type == 'lost' else (other, rep)
        comp = pair_components(lost, found)
        s = score_pair(comp)
        if s >= settings.MATCH_MIN_SCORE:
            scored.append((lost, found, comp, s))
            
    scored.sort(key=lambda t: -t[3])
    created = []
    for lost, found, comp, s in scored[:5]:
        exists = db.scalar(select(Match).where(Match.lost_id == lost.id, Match.found_id == found.id))
        if exists:
            continue
        m = Match(
            lost_id=lost.id,
            found_id=found.id,
            score=round(float(s), 4),
            confidence=confidence(s),
            components={k: (None if v is None else round(float(v), 4)) for k, v in comp.items()}
        )
        db.add(m)
        created.append(m)
        
    db.commit()
    return created
