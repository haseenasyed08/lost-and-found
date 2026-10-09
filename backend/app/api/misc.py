from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.security import current_user
from ..db import get_db
from ..models import AbuseReport, Notification, Place, User

router = APIRouter(tags=['misc'])

class AbuseIn(BaseModel):
    reason: str

@router.get('/places')
def get_places(db: Session = Depends(get_db)):
    return [
        {
            'id': p.id,
            'name': p.name,
            'latitude': p.latitude,
            'longitude': p.longitude
        }
        for p in db.scalars(select(Place).order_by(Place.name)).all()
    ]

@router.get('/notifications')
def get_notifications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    return [
        {
            'id': n.id,
            'text': n.text,
            'link': n.link,
            'read': n.read,
            'created_at': n.created_at.isoformat()
        }
        for n in rows
    ]

@router.post('/notifications/{nid}/read')
def mark_read(nid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    n = db.get(Notification, nid)
    if not n or n.user_id != user.id:
        raise HTTPException(404, 'Notification not found')
    n.read = True
    db.commit()
    return {'ok': True}

@router.post('/reports/{rid}/abuse')
def report_abuse(rid: int, body: AbuseIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    db.add(AbuseReport(reporter_id=user.id, report_id=rid, reason=body.reason[:300]))
    db.commit()
    return {'ok': True}
