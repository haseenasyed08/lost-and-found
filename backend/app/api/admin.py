import statistics
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..core.security import decrypt_json, hash_password, require_moderator
from ..db import get_db
from ..models import AbuseReport, Claim, Match, Place, Report, User
from ..schemas import report_out
from ..services.notify import audit, notify
from ..services.verification import new_handover_code, question_text

router = APIRouter(prefix='/admin', tags=['admin'])

class DecisionIn(BaseModel):
    decision: str  # approved | rejected

@router.get('/queue')
def queue(db: Session = Depends(get_db), mod: User = Depends(require_moderator)):
    claims = db.scalars(
        select(Claim).where(Claim.decision == 'manual_review').order_by(Claim.created_at)
    ).all()
    out = []
    for c in claims:
        found = c.match.found
        hidden = decrypt_json(found.hidden.payload) if found.hidden else {}
        given = decrypt_json(c.answers) if c.answers else {}
        keys = list(hidden.keys())[:3]
        rows = [
            {
                'question': question_text(found.category, k),
                'finder_detail': hidden.get(k, ''),
                'claimant_answer': given.get(k, '')
            }
            for k in keys
        ]
        out.append({
            'claim_id': c.id,
            'match_id': c.match_id,
            'claimant_name': c.match.lost.user_id,
            'found': report_out(found),
            'lost': report_out(c.match.lost),
            'rows': rows,
            'created_at': c.created_at.isoformat()
        })
        audit(db, mod.id, 'queue.view', 'claim', c.id)
    db.commit()
    return out

@router.post('/claims/{cid}/decision')
def decide(cid: int, body: DecisionIn, db: Session = Depends(get_db), mod: User = Depends(require_moderator)):
    c = db.get(Claim, cid)
    if not c or c.decision != 'manual_review':
        raise HTTPException(404, 'Claim not found or not in review queue')
    if body.decision not in ('approved', 'rejected'):
        raise HTTPException(400, 'decision must be approved or rejected')
        
    c.decision = body.decision
    c.decided_by = mod.id
    
    if body.decision == 'approved':
        code = new_handover_code()
        c.handover_hash = hash_password(code)
        c.match.status = 'claimed'
        c.match.found.status = 'claimed'
        notify(db, c.claimant_id, f'Verification approved by moderator! Your handover code is {code}. Show it to the finder.', f'/reports/{c.match.lost_id}')
        notify(db, c.match.found.user_id, 'An owner was approved by moderator. Arrange the handover and ask for their code.', f'/reports/{c.match.found_id}')
    else:
        notify(db, c.claimant_id, 'Your ownership claim could not be verified by the moderator.', f'/reports/{c.match.lost_id}')
        
    audit(db, mod.id, 'claim.decision', 'claim', c.id, decision=body.decision)
    db.commit()
    return {'ok': True, 'decision': body.decision}

@router.get('/abuse')
def list_abuse(db: Session = Depends(get_db), mod: User = Depends(require_moderator)):
    reports = db.scalars(select(AbuseReport).order_by(AbuseReport.created_at.desc()).limit(50)).all()
    return [
        {
            'id': a.id,
            'reporter_id': a.reporter_id,
            'report_id': a.report_id,
            'reason': a.reason,
            'created_at': a.created_at.isoformat()
        }
        for a in reports
    ]

@router.get('/analytics')
def analytics(db: Session = Depends(get_db), mod: User = Depends(require_moderator)):
    lost_total = db.scalar(select(func.count()).where(Report.type == 'lost')) or 0
    lost_closed = db.scalar(select(func.count()).where(Report.type == 'lost', Report.status == 'closed')) or 0
    found_total = db.scalar(select(func.count()).where(Report.type == 'found')) or 0
    matches_total = db.scalar(select(func.count()).select_from(Match)) or 0
    
    spans = db.execute(
        select(Report.created_at, Report.closed_at).where(Report.type == 'lost', Report.closed_at.is_not(None))
    ).all()
    hours = [(b - a).total_seconds() / 3600.0 for a, b in spans if b and a]
    
    by_cat = db.execute(
        select(Report.category, Report.type, func.count()).group_by(Report.category, Report.type)
    ).all()
    
    hotspots = db.execute(
        select(Place.name, func.count())
        .join(Report, Report.place_id == Place.id)
        .where(Report.type == 'lost')
        .group_by(Place.name)
        .order_by(func.count().desc())
    ).all()
    
    daily_rows = db.execute(
        select(func.date(Report.created_at), Report.type, func.count())
        .group_by(func.date(Report.created_at), Report.type)
        .order_by(func.date(Report.created_at))
    ).all()
    
    return {
        'recovery_rate': round(lost_closed / lost_total, 3) if lost_total else 0,
        'median_hours_to_recovery': round(statistics.median(hours), 1) if hours else None,
        'lost_total': lost_total,
        'lost_closed': lost_closed,
        'found_total': found_total,
        'matches_total': matches_total,
        'by_category': [{'category': c, 'type': t, 'count': n} for c, t, n in by_cat],
        'hotspots': [{'place': p, 'count': n} for p, n in hotspots],
        'daily': [{'date': str(d), 'type': t, 'count': n} for d, t, n in daily_rows],
    }
