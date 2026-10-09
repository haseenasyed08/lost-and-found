import io
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.security import current_user
from ..db import get_db
from ..models import Report, User
from ..schemas import report_out
from ..services.embeddings import embed_clip_text, embed_image, embed_text
from ..services.matching import CROSS_MODAL_SCALE, cosine

router = APIRouter(tags=['search'])

@router.post('/search')
async def search(
    text: str = Form(''),
    category: str = Form(''),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    has_text = bool(text.strip())
    has_img = image is not None and bool(image.filename)
    
    if not has_text and not has_img:
        raise HTTPException(400, 'Provide a description, a photo, or both')
        
    qt = embed_text(text) if has_text else None
    qc = embed_clip_text(text) if has_text else None
    
    qi = None
    if has_img:
        raw = await image.read()
        if raw:
            qi = embed_image(io.BytesIO(raw))
            
    q = select(Report).where(Report.type == 'found', Report.status == 'open')
    if category and category.strip():
        q = q.where(Report.category == category.strip())
        
    reports = db.scalars(q.limit(100)).all()
    out = []
    
    for r in reports:
        parts = []
        if qt is not None and r.txt_emb is not None:
            parts.append(cosine(qt, r.txt_emb))
            
        if qi is not None:
            if r.img_emb is not None:
                parts.append(cosine(qi, r.img_emb))
            elif r.clip_txt_emb is not None:
                parts.append(min(1.0, (cosine(qi, r.clip_txt_emb) or 0.0) * CROSS_MODAL_SCALE))
                
        if qc is not None and r.img_emb is not None:
            parts.append(min(1.0, (cosine(qc, r.img_emb) or 0.0) * CROSS_MODAL_SCALE))
            
        parts = [min(1.0, max(0.0, p)) for p in parts if p is not None]
        if parts:
            avg_score = sum(parts) / len(parts)
            out.append({**report_out(r), 'score': round(avg_score, 4)})
            
    out.sort(key=lambda d: -d['score'])
    return out[:30]
