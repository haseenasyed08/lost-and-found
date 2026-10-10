from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.security import current_user, decrypt_json, encrypt_json, hash_password, verify_password
from ..db import get_db
from ..models import Claim, Match, Report, User, now
from ..services.notify import audit, notify
from ..services.verification import decision_from, new_handover_code, question_text, score_answers

router = APIRouter(tags=['claims'])

class AnswersIn(BaseModel):
    answers: dict[str, str]

class CodeIn(BaseModel):
    code: str

def _keys(found: Report):
    if not found.hidden or not found.hidden.payload:
        return []
    payload = decrypt_json(found.hidden.payload)
    return list(payload.keys())[:3]

@router.post('/matches/{mid}/claim')
def start_claim(mid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    m = db.get(Match, mid)
    if not m:
        raise HTTPException(404, 'Match not found')
    if m.lost.user_id != user.id and user.role != 'moderator':
        raise HTTPException(403, 'Only the owner of the lost report can start a claim')
    if m.status in ('dismissed', 'closed') or m.found.status != 'open':
        raise HTTPException(400, 'This match is no longer available for claiming')
        
    c = db.scalar(select(Claim).where(Claim.match_id == mid, Claim.claimant_id == user.id))
    if c is None:
        c = Claim(match_id=mid, claimant_id=user.id)
        db.add(c)
        db.commit()
        db.refresh(c)
        
    if c.decision == 'approved':
        return {'claim_id': c.id, 'status': 'approved', 'handover_code': c.handover_plaintext, 'handover_instructions': m.found.handover_instructions}
    elif c.decision == 'manual_review':
        return {'claim_id': c.id, 'status': 'under_review'}
    elif c.attempts >= settings.MAX_CLAIM_ATTEMPTS:
        raise HTTPException(403, 'No verification attempts left for this match')
        
    keys = _keys(m.found)
    qs = [{'key': k, 'question': question_text(m.found.category, k)} for k in keys]
    return {
        'claim_id': c.id,
        'attempts_left': settings.MAX_CLAIM_ATTEMPTS - c.attempts,
        'questions': qs
    }

@router.post('/claims/{cid}/answers')
def submit_answers(cid: int, body: AnswersIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = db.get(Claim, cid)
    if not c or (c.claimant_id != user.id and user.role != 'moderator'):
        raise HTTPException(404, 'Claim not found')
    if c.attempts >= settings.MAX_CLAIM_ATTEMPTS or c.decision in ('approved', 'manual_review'):
        raise HTTPException(403, 'No verification attempts left')
        
    m, found = c.match, c.match.found
    hidden = decrypt_json(found.hidden.payload) if found.hidden else {}
    keys = _keys(found)
    
    result = score_answers(found.category, {k: hidden.get(k, '') for k in keys}, body.answers)
    n = sum(1 for v in result.values() if v)
    decision = decision_from(n, len(keys))
    
    c.attempts += 1
    c.n_correct = n
    c.decision = decision
    c.answers = encrypt_json(body.answers)
    
    code = None
    if decision == 'approved':
        code = new_handover_code()
        c.handover_hash = hash_password(code)
        c.handover_plaintext = code
        m.status = 'claimed'
        found.status = 'claimed'
        notify(db, found.user_id, 'An owner passed verification. Arrange the handover and ask for their code.', f'/reports/{found.id}')
    elif decision == 'manual_review':
        notify(db, found.user_id, 'A claim was submitted and is pending moderator review.', f'/reports/{found.id}')
        
    audit(db, user.id, 'claim.answers', 'claim', c.id, n_correct=n, decision=decision)
    db.commit()
    
    label_map = {'approved': 'approved', 'manual_review': 'under_review', 'rejected': 'not_verified'}
    return {
        'result': label_map.get(decision, 'not_verified'),
        'handover_code': code,
        'handover_instructions': found.handover_instructions,
        'attempts_left': max(0, settings.MAX_CLAIM_ATTEMPTS - c.attempts)
    }

@router.post('/claims/{cid}/confirm')
def confirm_handover(cid: int, body: CodeIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = db.get(Claim, cid)
    if not c:
        raise HTTPException(404, 'Claim not found')
    if c.match.found.user_id != user.id and user.role != 'moderator':
        raise HTTPException(403, 'Only the finder can confirm handover')
    if c.decision != 'approved' or not c.handover_hash:
        raise HTTPException(400, 'Claim is not in an approved state')
        
    if not verify_password(c.handover_hash, body.code.strip()):
        audit(db, user.id, 'handover.wrong_code', 'claim', c.id)
        db.commit()
        raise HTTPException(400, 'Invalid handover code. Please check with the owner.')
        
    m = c.match
    for r in (m.lost, m.found):
        r.status = 'closed'
        r.closed_at = now()
    m.status = 'closed'
    
    # Dismiss other competing matches
    db.execute(
        update(Match).where(
            (Match.lost_id == m.lost_id) | (Match.found_id == m.found_id),
            Match.id != m.id,
            Match.status == 'suggested'
        ).values(status='dismissed')
    )
    
    notify(db, m.lost.user_id, 'Handover confirmed! Your lost report is now closed.', f'/reports/{m.lost_id}')
    notify(db, m.found.user_id, 'Handover confirmed! Thank you for returning the item.', f'/reports/{m.found_id}')
    audit(db, user.id, 'handover.confirm', 'claim', c.id)
    db.commit()
    return {'ok': True, 'message': 'Handover successfully completed!'}
