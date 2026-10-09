from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.security import current_user, hash_password, make_token, verify_password
from ..db import get_db
from ..models import User

router = APIRouter(prefix='/auth', tags=['auth'])

class RegisterIn(BaseModel):
    email: str
    name: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

@router.post('/register')
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(400, 'Password must be at least 8 characters')
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'Email already registered')
    u = User(
        email=email,
        name=body.name.strip(),
        password_hash=hash_password(body.password)
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {
        'access_token': make_token(u.id, u.role),
        'token_type': 'bearer',
        'name': u.name,
        'email': u.email,
        'role': u.role
    }

@router.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
    # Support both JSON and Form submissions
    email = ''
    password = ''
    content_type = request.headers.get('content-type', '')
    if 'application/json' in content_type:
        data = await request.json()
        email = data.get('username') or data.get('email', '')
        password = data.get('password', '')
    else:
        form = await request.form()
        email = form.get('username') or form.get('email', '')
        password = form.get('password', '')
        
    u = db.scalar(select(User).where(User.email == str(email).strip().lower()))
    if not u or not verify_password(u.password_hash, str(password)):
        raise HTTPException(401, 'Wrong email or password')
    return {
        'access_token': make_token(u.id, u.role),
        'token_type': 'bearer',
        'name': u.name,
        'email': u.email,
        'role': u.role
    }

@router.get('/me')
def get_me(user: User = Depends(current_user)):
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role
    }

@router.post('/refresh')
def refresh(user: User = Depends(current_user)):
    return {
        'access_token': make_token(user.id, user.role),
        'token_type': 'bearer',
        'name': user.name,
        'role': user.role
    }
