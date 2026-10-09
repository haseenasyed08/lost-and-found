import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./lostfound.db')
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'caEsWan-XyYiCarjdKO5nroGZjLc0VF8lxDErc08-avim91a0K5oaVkRJposxiAy')
    JWT_MINUTES: int = 120
    FERNET_KEY: str = os.getenv('FERNET_KEY', 'VwZKPjphYzp7TfNl-BoFpkAnYWlBMSkeuI7qaHClOU0=')
    UPLOAD_DIR: str = os.getenv('UPLOAD_DIR', os.path.abspath('uploads'))
    MAX_UPLOAD_MB: int = 10
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000')
    MATCH_MIN_SCORE: float = 0.45
    MAX_CLAIM_ATTEMPTS: int = 2

    class Config:
        env_file = '.env'
        extra = 'ignore'

settings = Settings()
