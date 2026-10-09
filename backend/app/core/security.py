import datetime as dt
import json
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from .config import settings

ph = PasswordHasher()
oauth2 = OAuth2PasswordBearer(tokenUrl='/auth/login')

def hash_password(p: str) -> str:
    return ph.hash(p)

def verify_password(hashed: str, p: str) -> bool:
    try:
        return ph.verify(hashed, p)
    except (VerifyMismatchError, Exception):
        return False

def make_token(user_id: int, role: str) -> str:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.JWT_MINUTES)
    return jwt.encode({'sub': str(user_id), 'role': role, 'exp': exp}, settings.JWT_SECRET, algorithm='HS256')

def _fernet() -> Fernet:
    return Fernet(settings.FERNET_KEY.encode())

def encrypt_json(obj) -> bytes:
    return _fernet().encrypt(json.dumps(obj).encode())

def decrypt_json(blob: bytes):
    if not blob:
        return {}
    return json.loads(_fernet().decrypt(blob).decode())

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
    except jwt.PyJWTError:
        raise HTTPException(401, 'Invalid or expired token')
    user = db.get(User, int(data['sub']))
    if not user:
        raise HTTPException(401, 'User not found')
    return user

def require_moderator(user: User = Depends(current_user)) -> User:
    if user.role != 'moderator':
        raise HTTPException(403, 'Moderator access required')
    return user
