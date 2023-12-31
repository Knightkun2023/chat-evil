from .. import db

class SystemPrompts(db.Model):
    __tablename__ = 'system_prompts'

    # プロンプトのID。リビジョンと一緒に一意になる。
    prompt_id = db.Column(db.Integer, primary_key=True)
    # リビジョン番号
    revision = db.Column(db.Integer, primary_key=True)
    # プロンプト名。変更可能
    prompt_name = db.Column(db.String(30), nullable=False)
    # プロンプトの内容。
    prompt_content = db.Column(db.Text, nullable=False)
    # プロンプトの作成者・所有者。
    owner_user_no = db.Column(db.Integer, nullable=False)
    # 編集不可になっているか
    is_edit_locked = db.Column(db.Boolean, nullable=False)
    # 所有者以外の人が参照できるか
    is_viewable_by_everyone = db.Column(db.Boolean, nullable=False)
    # 所有者以外の人が編集できるか
    is_editable_by_everyone = db.Column(db.Boolean, nullable=False)
    # 最終編集者。このリビジョンを作った人
    updated_user_no = db.Column(db.Integer, nullable=False)
    # 最終更新日時。このリビジョンの作成日時
    updated_time = db.Column(db.String(17), nullable=False)
    # 削除されたか。
    is_deleted = db.Column(db.Boolean, nullable=False)

class Roleplayers(db.Model):
    __tablename__ = 'roleplayer'

    # RolePlayer番号
    roleplayer_no = db.Column(db.Integer, primary_key=True)
    # リビジョン番号
    revision = db.Column(db.Integer, primary_key=True)
    # このRolePlayer&revisionのUUID
    roleplayer_uuid = db.Column(db.String(64), unique=True, nullable=False)
    # RolePlayer名。変更可能
    roleplayer_name = db.Column(db.String(30), nullable=False)
    # メモ
    memo = db.Column(db.Text, nullable=True)
    # 顔写真はUUIDから作る。
    # Chatを開始するとき、ChatGPT側のセリフから始めるか
    assistant_first = db.Column(db.Boolean, nullable=False)

    # プロンプトのID。リビジョンと一緒に一意になる。
    prompt_id = db.Column(db.Integer, nullable=False)
    # リビジョン番号
    prompt_revision = db.Column(db.Integer, nullable=False)

    # RolePlayerの作成者・所有者。
    owner_user_no = db.Column(db.Integer, nullable=False)
    # 編集不可になっているか
    is_edit_locked = db.Column(db.Boolean, nullable=False)
    # 所有者以外の人が参照できるか
    is_viewable_by_everyone = db.Column(db.Boolean, nullable=False)
    # 所有者以外の人が編集できるか
    is_editable_by_everyone = db.Column(db.Boolean, nullable=False)
    # 最終編集者。このリビジョンを作った人
    updated_user_no = db.Column(db.Integer, nullable=False)
    # 最終更新日時。このリビジョンの作成日時
    updated_time = db.Column(db.String(17), nullable=False)
    # 削除されたか。
    is_deleted = db.Column(db.Boolean, nullable=False)
