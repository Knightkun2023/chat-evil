from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from typing import Optional
from .. import db

bcrypt = Bcrypt()

class LoginUser(UserMixin, db.Model):
    __tablename__ = 'login_users'
    # ユーザー番号。他のユーザーには公開されない。
    user_no: int = db.Column(db.Integer, primary_key=True)
    # ユーザー情報のリビジョン
    revision: int = db.Column(db.Integer, primary_key=True)
    # ユーザーID。ログイン時に使用。ユーザー登録時に重複しないようにチェックされる。他のユーザーには公開されない。
    user_id: str = db.Column(db.String(30), nullable=False)
    # パスワードのハッシュ
    password_hash: str = db.Column(db.String(128), nullable=False)
    # ユーザー名。他のユーザーに公開されうる。
    user_name: str = db.Column(db.String(30), nullable=False)
    # ユーザーのロールを表す数値
    roles: int = db.Column(db.Integer, nullable=False)
    # このリビジョンの登録日時
    updated_time: str = db.Column(db.String(17), nullable=False)

    def set_password(self, password: str) -> None:
        '''
        パスワードを設定する。
        '''
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        '''
        入力されたパスワードが正しいかチェックする。
        '''
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_id(self) -> str:
        '''
        Flask-Login用のユーザーID
        ユーザーはユーザー番号とリビジョンで一意に決まる。
        '''
        return f"{self.user_no}#{self.revision}"

class RegistrationCode(db.Model):
    __tablename__ = 'registration_codes'
    # 登録コード
    registration_code: str = db.Column(db.String(64), unique=True, primary_key=True)
    # 備考。誰のために発行したか、などを記載。
    remarks: str = db.Column(db.String(128), nullable=False)
    # 使用済みフラグ
    is_used: bool = db.Column(db.Boolean, nullable=False)
    # 登録コードを発行したユーザーの番号
    issuing_user_no: int = db.Column(db.Integer, nullable=False)
    # 登録コードを発行した日時
    issuing_time: str = db.Column(db.String(17), nullable=False)
    # 有効期限。直接入力しなかった場合は発行した日時からconfigで指定した時間だけ後の日時が設定される
    expiration_time: str = db.Column(db.String(17), nullable=False)
    # この登録コードを使ってユーザー登録が行われた日時
    register_time: Optional[str] = db.Column(db.String(17), nullable=True)
    # この登録コードを使って登録されたユーザーの番号
    registered_user_no: Optional[int] = db.Column(db.Integer, nullable=True)
    # 削除フラグ
    is_deleted: bool = db.Column(db.Boolean, nullable=False)
    # 削除フラグが設定された日時
    deleted_time: Optional[str] = db.Column(db.String(17), nullable=True)
    # この登録コードで登録されるユーザーのロールを表す数値
    roles: int = db.Column(db.Integer, nullable=False)

class LoginHistory(db.Model):
    '''
    ログイン履歴
    '''
    __tablename__ = 'login_history'
    # シーケンス
    seq: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ログインに成功したユーザーの番号
    user_no: Optional[int] = db.Column(db.Integer, nullable=True)
    # ログイン時に入力されたユーザーID
    user_id: str = db.Column(db.String(30), nullable=False)
    # ログインが実行された日時
    login_time: str = db.Column(db.String(17), nullable=False)
    # ログインが実行された時のUser-Agent
    user_agent: str = db.Column(db.String(512), nullable=False)
    # ログインが実行された時のリモートIPアドレス
    remote_ip: str = db.Column(db.String(128), nullable=False)
    # ログインの成否
    is_success: bool = db.Column(db.Boolean, nullable=False)
