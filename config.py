import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-genai-cafe-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@cafe.com'
    STAFF_EMAIL = os.environ.get('STAFF_EMAIL') or 'staff@cafe.com'

    # ── Mail (Gmail SMTP) ─────────────────────────────────────────────────────
    MAIL_HOST       = os.environ.get('MAIL_HOST', 'smtp.gmail.com')
    MAIL_PORT       = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME   = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD   = os.environ.get('MAIL_PASSWORD', '')
    MAIL_FROM_NAME  = os.environ.get('MAIL_FROM_NAME', 'HRD Cafe')
    MAIL_FROM_EMAIL = os.environ.get('MAIL_FROM_EMAIL', '')


class DevelopmentConfig(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:123456789%40@localhost:3306/cafe"
    )


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig
}