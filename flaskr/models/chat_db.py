from .. import db
from typing import Optional

class ChatHistory(db.Model):
    '''
    チャット履歴。1回のチャットの内容を保存する。
    '''
    __tablename__ = 'chat_history'
    # シーケンス。全てのチャットを通して一連に振るシーケンス。
    seq = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # チャット番号。チャットの一連のやり取りを一意に決める.
    chat_no = db.Column(db.Integer, nullable=False, index=True)
    # system, user, assistantといったロール
    role = db.Column(db.String(30), nullable=False)
    # 送った、または受信した内容
    content = db.Column(db.Text, nullable=False)
    # 使用したChatGPTモデルのID
    model_id: Optional[int] = db.Column(db.Integer, nullable=True)
    # メッセージの主体の名前
    name = db.Column(db.Text, nullable=True)
    # チャット日時
    chat_time: str = db.Column(db.String(17), nullable=False)
    # モデレーションカラー。OK:空、オレンジ：O, 赤：R
    moderation_color: Optional[str] = db.Column(db.String(1), nullable=True)
    # モデレーション結果
    moderation_result_original: Optional[str] = db.Column(db.Text, nullable=True)
    # sexualのフラグ
    moderation_sexual_flagged: Optional[bool] = db.Column(db.Boolean, nullable=True)
    # sexualのスコア
    moderation_sexual_score: Optional[float] = db.Column(db.REAL, nullable=True)
    # sexual/minorsのフラグ
    moderation_sexual_minors_flagged: Optional[bool] = db.Column(db.Boolean, nullable=True)
    # sexual/minorsのスコア
    moderation_sexual_minors_score: Optional[float] = db.Column(db.REAL, nullable=True)
    # 編集フラグ
    is_updated: bool = db.Column(db.Boolean, nullable=False, default=False)
    # 削除フラグ
    is_deleted: bool = db.Column(db.Boolean, nullable=False, default=False)

class ChatInfo(db.Model):
    '''
    一連のチャットの情報
    '''
    __tablename__ = 'chat_info'
    # チャット番号
    chat_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # チャットID。チャット番号と1対1になるUUID。改ざん防止のためにチャット番号の代わりに画面側に渡すことができるID。
    chat_uuid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    # チャット名
    chat_name = db.Column(db.String(30), nullable=False)
    # ユーザー番号
    user_no = db.Column(db.Integer, nullable=False)
    # assistantの顔写真
    assistant_pic_url: str = db.Column(db.Text, nullable=True)
    # 更新日時
    updated_time: str = db.Column(db.String(17), nullable=False)
    # 削除フラグ
    is_deleted: bool = db.Column(db.Boolean, nullable=False, default=False)
    # 削除フラグが設定された日時
    deleted_time: Optional[str] = db.Column(db.String(17), nullable=True)

class WordReplacing(db.Model):
    '''
    クライアント側の入力・表示する文言と、サーバー側でChatGPTに送る・取得する文言のうち、置換するワードのペアを定義する。
    '''
    __tablename__ = 'word_replacings'
    # シーケンス。全てのペアを通して一連に振るシーケンス。
    seq = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # チャット番号。チャットの一連のやり取りを一意に決める.
    chat_no = db.Column(db.Integer, nullable=False, index=True)
    # Assistantフラグ。Userのchatの場合はFalse、Assistantのchatの場合はTrue
    is_assistant: bool = db.Column(db.Boolean, nullable=False, default=False)
    # ブラウザ側のワード
    word_client = db.Column(db.String(50), nullable=False)
    # サーバー側のワード
    word_server = db.Column(db.String(50), nullable=False)
    # ユーザー番号
    user_no = db.Column(db.Integer, nullable=False)
    # 更新日時
    updated_time: str = db.Column(db.String(17), nullable=False)
    # 削除フラグ
    is_deleted: bool = db.Column(db.Boolean, nullable=False, default=False)
    # 削除フラグが設定された日時
    deleted_time: Optional[str] = db.Column(db.String(17), nullable=True)
