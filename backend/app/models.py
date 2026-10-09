import datetime as dt
from sqlalchemy import (
    JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer,
    LargeBinary, String, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .core.config import settings

IMG_DIM, TXT_DIM = 512, 384

def now():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

class Base(DeclarativeBase):
    pass

is_postgres = 'postgresql' in settings.DATABASE_URL
has_pgvector = False

if is_postgres:
    try:
        from pgvector.sqlalchemy import Vector
        VectorTypeImg = Vector(IMG_DIM)
        VectorTypeTxt = Vector(TXT_DIM)
        has_pgvector = True
    except ImportError:
        VectorTypeImg = JSON
        VectorTypeTxt = JSON
else:
    VectorTypeImg = JSON
    VectorTypeTxt = JSON

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='user')  # user | moderator
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

class Place(Base):
    __tablename__ = 'places'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

class Report(Base):
    __tablename__ = 'reports'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    type: Mapped[str] = mapped_column(String(10), index=True)  # lost | found
    category: Mapped[str] = mapped_column(String(40), index=True)
    group: Mapped[str] = mapped_column(String(40), index=True)
    brand: Mapped[str] = mapped_column(String(80), default='')
    color: Mapped[str] = mapped_column(String(40), default='')
    description: Mapped[str] = mapped_column(Text)
    place_id: Mapped[int] = mapped_column(ForeignKey('places.id'))
    event_time: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    time_window_hours: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default='open', index=True)  # open | claimed | closed
    ocr_text: Mapped[str] = mapped_column(Text, default='')
    
    img_emb = mapped_column(VectorTypeImg, nullable=True)          # CLIP image (512-d)
    clip_txt_emb = mapped_column(VectorTypeImg, nullable=True)     # CLIP text cross-modal (512-d)
    txt_emb = mapped_column(VectorTypeTxt, nullable=True)          # multilingual text (384-d)
    
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    
    place = relationship('Place')
    images = relationship('ReportImage', back_populates='report', cascade='all, delete-orphan')
    hidden = relationship('HiddenDetail', uselist=False, cascade='all, delete-orphan')

    if has_pgvector:
        __table_args__ = (
            Index('ix_reports_img', 'img_emb', postgresql_using='hnsw', postgresql_ops={'img_emb': 'vector_cosine_ops'}),
            Index('ix_reports_txt', 'txt_emb', postgresql_using='hnsw', postgresql_ops={'txt_emb': 'vector_cosine_ops'}),
        )

class ReportImage(Base):
    __tablename__ = 'report_images'
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey('reports.id'), index=True)
    private_path: Mapped[str] = mapped_column(String(300))  # original, never served publicly
    public_path: Mapped[str] = mapped_column(String(300))   # faces blurred, metadata stripped
    report = relationship('Report', back_populates='images')

class HiddenDetail(Base):
    __tablename__ = 'hidden_details'
    report_id: Mapped[int] = mapped_column(ForeignKey('reports.id'), primary_key=True)
    payload: Mapped[bytes] = mapped_column(LargeBinary)  # Fernet-encrypted JSON {key: value}

class Match(Base):
    __tablename__ = 'matches'
    id: Mapped[int] = mapped_column(primary_key=True)
    lost_id: Mapped[int] = mapped_column(ForeignKey('reports.id'), index=True)
    found_id: Mapped[int] = mapped_column(ForeignKey('reports.id'), index=True)
    score: Mapped[float] = mapped_column(Float)
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[str] = mapped_column(String(10))  # high | medium | low
    status: Mapped[str] = mapped_column(String(20), default='suggested')  # suggested | dismissed | claimed | closed
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    
    lost = relationship('Report', foreign_keys=[lost_id])
    found = relationship('Report', foreign_keys=[found_id])
    __table_args__ = (UniqueConstraint('lost_id', 'found_id'),)

class Claim(Base):
    __tablename__ = 'claims'
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey('matches.id'), index=True)
    claimant_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    answers: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)  # encrypted
    n_correct: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    decision: Mapped[str] = mapped_column(String(20), default='pending')  # pending | approved | manual_review | rejected
    handover_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    
    match = relationship('Match')

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    text: Mapped[str] = mapped_column(String(300))
    link: Mapped[str] = mapped_column(String(200), default='')
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

class AbuseReport(Base):
    __tablename__ = 'abuse_reports'
    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    report_id: Mapped[int] = mapped_column(ForeignKey('reports.id'))
    reason: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
