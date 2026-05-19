import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'atomquest-hackathon-secret-key-2026')
    # Auto-detect Railway Persistent Volume
    railway_volume = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    if railway_volume:
        default_db_uri = 'sqlite:///' + os.path.join(railway_volume, 'goaltracker.db')
    else:
        default_db_uri = 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'goaltracker.db')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', default_db_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-atomquest-secret-2026')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_SUBJECT_CLAIM_ALLOW_INT = True

    # Caching Config
    CACHE_TYPE = 'RedisCache' if os.environ.get('REDIS_URL') else 'SimpleCache'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = 3600
