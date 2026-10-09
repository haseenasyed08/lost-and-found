import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from .api import admin, auth, claims, misc, reports, search
from .core.config import settings
from .db import engine
from .models import Base, is_postgres
from .services import matching

public_dir = os.path.join(settings.UPLOAD_DIR, 'public')
private_dir = os.path.join(settings.UPLOAD_DIR, 'private')
os.makedirs(public_dir, exist_ok=True)
os.makedirs(private_dir, exist_ok=True)

app = FastAPI(
    title='Lost & Found Intelligence API',
    description='Multimodal AI-powered lost and found matching with ownership verification',
    version='1.0.0'
)

# Configure CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount public images folder
app.mount('/files/public', StaticFiles(directory=public_dir), name='files')

# Include API routers
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(claims.router)
app.include_router(admin.router)
app.include_router(misc.router)

@app.on_event('startup')
def startup():
    if is_postgres:
        try:
            with engine.begin() as conn:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        except Exception as e:
            print(f"Notice on vector extension: {e}")
            
    Base.metadata.create_all(engine)
    
    # Load trained LightGBM ranker if available
    ranker_path = os.path.join(os.path.dirname(__file__), 'data', 'ranker.txt')
    if os.path.exists(ranker_path):
        predictor = matching.load_ranker(ranker_path)
        if predictor:
            matching.RANKER = predictor
            print("Successfully loaded trained LightGBM ranker model.")

@app.get('/health')
def health():
    return {'status': 'ok', 'app': 'Lost & Found Intelligence'}

# Serve frontend build if available
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist'))
if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, 'assets')
    if os.path.exists(assets_dir):
        app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

    @app.get('/{full_path:path}')
    async def serve_spa(full_path: str):
        # Don't hijack API or docs routes
        if full_path.startswith(('auth', 'reports', 'search', 'claims', 'admin', 'places', 'notifications', 'files', 'docs', 'openapi.json', 'health')):
            return None
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, 'index.html'))

# Trigger reload
