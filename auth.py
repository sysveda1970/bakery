import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash
from models import User, StoreSetting, db


def hash_password(password):
    """パスワードをハッシュ化"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def check_password(password, password_hash):
    """パスワードを検証"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def login_required(f):
    """ログインが必要なルートのデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインが必要です', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def create_user(username, store_name, password):
    """新規ユーザーを作成"""
    try:
        # ユーザー名の重複チェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return None, 'このユーザーIDは既に使用されています'

        # パスワードのハッシュ化
        password_hash = hash_password(password)

        # ユーザーの作成
        user = User(
            username=username,
            store_name=store_name,
            password_hash=password_hash
        )
        db.session.add(user)
        db.session.flush()  # user.idを取得するため

        # 店舗設定の初期化
        store_setting = StoreSetting(user_id=user.id)
        db.session.add(store_setting)

        db.session.commit()
        return user, None

    except Exception as e:
        db.session.rollback()
        return None, f'ユーザー登録に失敗しました: {str(e)}'


def authenticate_user(username, password):
    """ユーザーを認証"""
    user = User.query.filter_by(username=username).first()

    if user and check_password(password, user.password_hash):
        return user
    return None


def get_current_user():
    """現在ログイン中のユーザーを取得"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None
