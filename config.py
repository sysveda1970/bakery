import os

class Config:
    """アプリケーション設定クラス"""

    # セキュリティ設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # データベース設定
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # セッション設定
    PERMANENT_SESSION_LIFETIME = 3600  # 1時間
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # アプリケーション設定
    ITEMS_PER_PAGE = 20
