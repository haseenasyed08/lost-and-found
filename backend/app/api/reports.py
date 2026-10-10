import datetime as dt
import json
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from ..core.security import current_user, encrypt_json
from ..db import SessionLocal, get_db
from ..models import Claim, HiddenDetail, Match, Place, Report, ReportImage, User
from ..schemas import report_out
from ..services.embeddings import embed_clip_text, embed_image, embed_text
from ..services.imaging import ocr_text, save_image
from ..services.matching import run_matching
from ..services.notify import audit, notify
from ..services.verification import QUESTIONS

router = APIRouter(prefix='/reports', tags=['reports'])

def process_matches(report_id: int):
    db = SessionLocal()
    try:
        matches = run_matching(db, report_id)
        for m in matches:
            notify(db, m.lost.user_id, 'Potential match found for your lost item', f'/reports/{m.lost_id}')
            notify(db, m.found.user_id, 'A possible owner exists for the item you found', f'/reports/{m.found_id}')
        db.commit()
    except Exception as e:
        print(f"Error processing background matches: {e}")
    finally:
        db.close()

@router.get('/categories')
def categories():
    return {
        c: {
            'group': v['group'],
            'questions': {k: q['q'] for k, q in v['questions'].items()}
        }
        for c, v in QUESTIONS.items()
    }

@router.get('/mine')
def my_reports(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
    ).all()
    return [report_out(r, owner=True) for r in rows]

@router.post('')
async def create_report(
    background: BackgroundTasks,
    type: str = Form(...),
    category: str = Form(...),
    brand: str = Form(''),
    color: str = Form(''),
    description: str = Form(...),
    place_id: int = Form(...),
    event_time: str = Form(...),
    time_window_hours: float = Form(1.0),
    handover_instructions: str = Form(None),
    hidden_details: str = Form('{}'),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if type not in ('lost', 'found'):
        raise HTTPException(400, 'type must be lost or found')
    if len(description.strip()) < 8:
        raise HTTPException(400, 'Please describe the item in at least 8 characters')
        
    try:
        # parse datetime (handles ISO string from HTML input)
        event_dt = dt.datetime.fromisoformat(event_time.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        raise HTTPException(400, 'Invalid event_time format')
        
    if event_dt > dt.datetime.utcnow() + dt.timedelta(hours=24):
        raise HTTPException(400, 'Time cannot be in the future')
        
    if not db.get(Place, place_id):
        raise HTTPException(404, 'Unknown place')
        
    group = QUESTIONS.get(category, {}).get('group', 'other')
    rep = Report(
        user_id=user.id,
        type=type,
        category=category,
        group=group,
        brand=brand.strip(),
        color=color.strip().lower(),
        description=description.strip(),
        place_id=place_id,
        event_time=event_dt,
        time_window_hours=time_window_hours,
        handover_instructions=handover_instructions.strip() if handover_instructions else None
    )
    
    rep.txt_emb = embed_text(rep.description)
    rep.clip_txt_emb = embed_clip_text(rep.description)
    db.add(rep)
    db.flush()
    
    if image is not None and image.filename:
        content = await image.read()
        if content:
            content_type = image.content_type or 'image/jpeg'
            private, public = save_image(content, content_type)
            rep.img_emb = embed_image(private)
            rep.ocr_text = ocr_text(private)
            db.add(ReportImage(report_id=rep.id, private_path=private, public_path=public))
            
    if type == 'found':
        try:
            raw = json.loads(hidden_details) if isinstance(hidden_details, str) else hidden_details
        except Exception:
            raise HTTPException(400, 'hidden_details must be JSON')
            
        allowed = QUESTIONS.get(category, {}).get('questions', {})
        clean = {k: str(v).strip() for k, v in raw.items() if k in allowed and str(v).strip()}
        if len(clean) < 3:
            raise HTTPException(400, 'Please answer at least 3 private questions about the item for ownership verification')
        db.add(HiddenDetail(report_id=rep.id, payload=encrypt_json(clean)))
        
    audit(db, user.id, 'report.create', 'report', rep.id, type=type)
    db.commit()
    db.refresh(rep)
    
    background.add_task(process_matches, rep.id)
    return report_out(rep, owner=True)

@router.get('/{rid}')
def get_report(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.get(Report, rid)
    if not r:
        raise HTTPException(404, 'Not found')
    return report_out(r, owner=(r.user_id == user.id))

@router.get('/{rid}/matches')
def report_matches(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.get(Report, rid)
    if not r:
        raise HTTPException(404, 'Report not found')
    if r.user_id != user.id and user.role != 'moderator':
        raise HTTPException(403, 'Access denied')
        
    rows = db.scalars(
        select(Match).where(
            or_(Match.lost_id == rid, Match.found_id == rid),
            Match.status != 'dismissed'
        ).order_by(Match.score.desc())
    ).all()
    
    out = []
    for m in rows:
        other = m.found if m.lost_id == rid else m.lost
        claim = db.scalar(
            select(Claim).where(Claim.match_id == m.id, Claim.decision == 'approved')
        )
        out.append({
            'match_id': m.id,
            'score': m.score,
            'confidence': m.confidence,
            'components': m.components,
            'status': m.status,
            'claim_id': claim.id if claim else None,
            'other': report_out(other, owner=False)
        })
    return out

@router.post('/matches/{mid}/dismiss')
def dismiss(mid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    m = db.get(Match, mid)
    if not m or (user.id not in (m.lost.user_id, m.found.user_id) and user.role != 'moderator'):
        raise HTTPException(404, 'Not found')
    m.status = 'dismissed'
    audit(db, user.id, 'match.dismiss', 'match', m.id)
    db.commit()
    return {'ok': True}
