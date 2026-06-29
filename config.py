import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'scholarsync.db')}",
    )


class ProductionConfig(Config):
    DEBUG = False
    @staticmethod
    def _get_db_url():
        url = os.environ.get("DATABASE_URL", "")
        return url.replace("postgres://", "postgresql://", 1) if url else None
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1) or None


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
