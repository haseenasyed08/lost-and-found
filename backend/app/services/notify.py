from ..models import AuditLog, Notification

def notify(db, user_id: int, text: str, link: str = ''):
    n = Notification(user_id=user_id, text=text, link=link)
    db.add(n)
    return n

def audit(db, actor_id: int | None, action: str, entity: str, entity_id: int | None = None, **detail):
    log = AuditLog(actor_id=actor_id, action=action, entity=entity, entity_id=entity_id, detail=detail)
    db.add(log)
    return log
