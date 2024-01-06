from flask import session, render_template, request, url_for, jsonify
from . import app, db
from .models.system_prompts_db import SystemPrompts
from .models.login_db import LoginUser
from sqlalchemy import func
from sqlalchemy.orm import aliased
from flask_login import login_required, current_user
from .utils.commons import is_empty, generate_random_string, is_numeric, get_current_time, checkbox_to_save
import json, logging

@app.route('/prompt/list', methods=['GET'])
@login_required
def system_prompt_list():

    # 閲覧ユーザのユーザ番号
    current_user_no = current_user.user_no

    # LoginUserテーブルのエイリアスを作成
    owner_user = aliased(LoginUser, name="owner_user")
    updated_user = aliased(LoginUser, name="updated_user")

    # 各prompt_idの最大revisionを取得するサブクエリを作成
    subquery = db.session.query(
        SystemPrompts.prompt_id,
        func.max(SystemPrompts.revision).label("max_revision")
    ).group_by(SystemPrompts.prompt_id).subquery()

    system_prompts = db.session.query(SystemPrompts, owner_user.user_name, updated_user.user_name, 
                                      (SystemPrompts.owner_user_no == current_user_no).label("is_owner")).join(
        subquery, 
        db.and_(
            SystemPrompts.prompt_id == subquery.c.prompt_id,
            SystemPrompts.revision == subquery.c.max_revision
        )
    ).outerjoin(
        owner_user,
        owner_user.user_no == SystemPrompts.owner_user_no
    ).outerjoin(
        updated_user,
        updated_user.user_no == SystemPrompts.updated_user_no
    ).filter(
        SystemPrompts.is_deleted == False,
        db.or_(
            SystemPrompts.owner_user_no == current_user_no,
            SystemPrompts.is_viewable_by_everyone == True
        )
    ).order_by(SystemPrompts.updated_time.desc()).all()

    return render_template("system_prompt_list.html", system_prompts=system_prompts)

@app.route('/prompt/', defaults={'prompt_id': None}, methods=['GET'])
@app.route('/prompt/<int:prompt_id>', methods=['GET'])
@login_required
def system_prompt_detail_show(prompt_id):

    csrf_token = generate_random_string(48)  # CSRF対策にランダムなシークレットキーを設定
    session['system_prompt_csrf_token'] = csrf_token

    if is_empty(prompt_id):
        # 新規登録
        return render_template("system_prompt.html", system_prompt={}, csrf_token=csrf_token)

    # 閲覧ユーザのユーザ番号
    current_user_no = current_user.user_no

    # 各prompt_idの最大revisionを取得するサブクエリを作成
    subquery = db.session.query(
        SystemPrompts.prompt_id,
        func.max(SystemPrompts.revision).label("max_revision")
    ).filter(SystemPrompts.prompt_id == prompt_id
    ).group_by(SystemPrompts.prompt_id).subquery()

    # LoginUserテーブルのエイリアスを作成
    owner_user = aliased(LoginUser, name="owner_user")
    updated_user = aliased(LoginUser, name="updated_user")

    system_prompt = db.session.query(SystemPrompts, owner_user.user_name, updated_user.user_name, 
                                      (SystemPrompts.owner_user_no == current_user_no).label("is_owner"),
                                      (db.or_(SystemPrompts.owner_user_no == current_user_no, SystemPrompts.is_editable_by_everyone == True)).label("is_editable")).join(
        subquery, 
        db.and_(
            SystemPrompts.prompt_id == subquery.c.prompt_id,
            SystemPrompts.revision == subquery.c.max_revision
        )
    ).outerjoin(
        owner_user,
        owner_user.user_no == SystemPrompts.owner_user_no
    ).outerjoin(
        updated_user,
        updated_user.user_no == SystemPrompts.updated_user_no
    ).filter(
        SystemPrompts.is_deleted == False,
        db.or_(
            SystemPrompts.owner_user_no == current_user_no,
            SystemPrompts.is_viewable_by_everyone == True
        )
    ).order_by(SystemPrompts.updated_time.desc()).first()

    if not system_prompt:
        # prompt_idが間違っている
        return render_template("system_prompt.html", main_error_message='指定したプロンプトが見つかりませんでした。', system_prompt={}, csrf_token=csrf_token), 404

    # シリアル化可能な形に変換
    system_prompt_data = {
        'prompt_id': system_prompt[0].prompt_id,
        'revision': system_prompt[0].revision,
        'prompt_name': system_prompt[0].prompt_name,
        'prompt_content': system_prompt[0].prompt_content,
        'is_edit_locked': system_prompt[0].is_edit_locked,
        'is_viewable_by_everyone': system_prompt[0].is_viewable_by_everyone,
        'is_editable_by_everyone': system_prompt[0].is_editable_by_everyone,
        'updated_time': system_prompt[0].updated_time
    }

    detail_data = {
        "SystemPrompts": system_prompt_data,
        "owner_user": system_prompt[1],
        "updated_user": system_prompt[2],
        "is_owner": system_prompt[3],
        "is_editable": system_prompt[4]
    }
    system_prompt_json = json.dumps(detail_data, default=str)
    return render_template("system_prompt.html", system_prompt=detail_data, serialized_json=system_prompt_json, csrf_token=csrf_token)

@app.route('/prompt/', methods=['POST'])
@login_required
def system_prompt_detail():
    app_logger = logging.getLogger('app_logger')

    # パラメータを受け取る
    data = request.get_json()
    csrf_token = data['csrf_token']

    # CSRFトークンのチェック
    if not session['system_prompt_csrf_token'] == csrf_token:
        dic = {}
        dic['main_error_message'] = 'Invalid access.'
        return jsonify(dic), 403  # 不正なアクセス
    
    prompt_name = '' if not 'prompt_name' in data else data['prompt_name']
    prompt_content = '' if not 'prompt_content' in data else data['prompt_content']
    is_edit_locked = '' if not 'is_edit_locked' in data else data['is_edit_locked']
    is_viewable_by_everyone = '' if not 'is_viewable_by_everyone' in data else data['is_viewable_by_everyone']
    is_editable_by_everyone = '' if not 'is_editable_by_everyone' in data else data['is_editable_by_everyone']
    prompt_id = '' if not 'prompt_id' in data else data['prompt_id']
    revision = '' if not 'revision' in data else data['revision']
    updated_time = '' if not 'updated_time' in data else data['updated_time']

    # parameter check
    error_msgs = {}
    if not is_empty(prompt_id) and not is_numeric(prompt_id):
        error_msgs['prompt_id'] = 'Invalid prompt_id.'
    if len(prompt_name) < 1 or len(prompt_name) > 30:
        error_msgs['prompt_name'] = 'Invalid prompt name.'
    if not is_empty(is_edit_locked) and not is_numeric(is_edit_locked):
        error_msgs['main_error_message'] = 'Invalid access.'
    if not is_empty(is_viewable_by_everyone) and not is_numeric(is_viewable_by_everyone):
        error_msgs['main_error_message'] = 'Invalid access.'
    if not is_empty(is_editable_by_everyone) and not is_numeric(is_editable_by_everyone):
        error_msgs['main_error_message'] = 'Invalid access.'

    if error_msgs:
        return jsonify(dic), 400

    if prompt_id == '0' and revision == '0' and updated_time == '0':
        # 新規登録
        rs = db.session.query(
            func.max(SystemPrompts.prompt_id).label('max_prompt_id')
        ).one_or_none()
        app_logger.debug(f'@@@@@@@@@@@ rs={rs}')
        prompt_id = 1
        if rs:
            prompt_id = prompt_id + rs[0]

        prompt = SystemPrompts(
                    prompt_id=prompt_id,
                    revision=1,
                    prompt_name=prompt_name,
                    prompt_content=prompt_content, 
                    is_edit_locked=checkbox_to_save(is_edit_locked),
                    is_viewable_by_everyone=checkbox_to_save(is_viewable_by_everyone),
                    is_editable_by_everyone=checkbox_to_save(is_editable_by_everyone),
                    owner_user_no=current_user.user_no,
                    updated_user_no=current_user.user_no,
                    is_deleted=False,
                    updated_time=get_current_time())
        db.session.add(prompt)
        db.session.commit()

        return jsonify({'redirect': url_for('system_prompt_detail_show', prompt_id=prompt_id, main_error_message='登録しました。')})


    # 既存のデータを更新
    try:
        # prompt_idの最大revisionを取得するサブクエリを作成
        subquery = db.session.query(
            SystemPrompts.prompt_id,
            func.max(SystemPrompts.revision).label("max_revision")
        ).filter(SystemPrompts.prompt_id == prompt_id
        ).group_by(SystemPrompts.prompt_id).subquery()

        system_prompt = db.session.query(SystemPrompts).join(
            subquery, 
            db.and_(
                SystemPrompts.prompt_id == subquery.c.prompt_id,
                SystemPrompts.revision == subquery.c.max_revision
            )
        ).filter(
            SystemPrompts.is_deleted == False,
            SystemPrompts.revision == revision,
            SystemPrompts.updated_time == updated_time,
            db.or_(
                SystemPrompts.owner_user_no == current_user.user_no,
                SystemPrompts.is_editable_by_everyone == 1
            )
        ).first()

        if not system_prompt:
            # データはcurrent_userが変更できない状態である。
            error_msgs['main_error_message'] = '変更ができませんでした。'
            return jsonify(error_msgs), 400

        # 新しいrevisionで追加する。
        prompt = SystemPrompts(
                    prompt_id=prompt_id,
                    revision=int(revision) + 1,
                    prompt_content=prompt_content, 
                    owner_user_no=system_prompt.owner_user_no,
                    updated_user_no=current_user.user_no,
                    is_deleted=False,
                    updated_time=get_current_time())

        if system_prompt.owner_user_no == current_user.user_no:
            # オーナーの場合に変更できる項目
            prompt.prompt_name = prompt_name
            prompt.is_edit_locked = checkbox_to_save(is_edit_locked)
            prompt.is_viewable_by_everyone = checkbox_to_save(is_viewable_by_everyone)
            prompt.is_editable_by_everyone = checkbox_to_save(is_editable_by_everyone)

        db.session.add(prompt)
        db.session.commit()

        return jsonify({'redirect': url_for('system_prompt_detail_show', prompt_id=prompt_id, main_error_message='更新しました。')})
    except Exception as e:
        # エラーが発生した。
        app_logger.exception('システムプロンプトの更新に失敗しました。')
        error_msgs['main_error_message'] = 'エラーが発生しました。'
        return jsonify(error_msgs), 500

@app.route('/prompt/delete', methods=['POST'])
@login_required
def delete_prompt():
    app_logger = logging.getLogger('app_logger')

    # パラメータを受け取る
    data = request.get_json()
    csrf_token = data['csrf_token']

    # CSRFトークンのチェック
    if not session['system_prompt_csrf_token'] == csrf_token:
        dic = {}
        dic['main_error_message'] = 'Invalid access.'
        return jsonify(dic), 403  # 不正なアクセス

    prompt_id = '' if not 'prompt_id' in data else data['prompt_id']
    revision = '' if not 'revision' in data else data['revision']
    updated_time = '' if not 'updated_time' in data else data['updated_time']

    # parameter check
    error_msgs = {}
    if not is_empty(prompt_id) and not is_numeric(prompt_id):
        error_msgs['prompt_id'] = 'Invalid prompt_id.'
    if not is_empty(revision) and not is_numeric(revision):
        error_msgs['revision'] = 'Invalid revision.'
    if not is_empty(updated_time) and not is_numeric(updated_time):
        error_msgs['updated_time'] = 'Invalid updated_time.'

    if error_msgs:
        error_msgs['main_error_message'] = 'Invalid parameters.'
        app_logger.warn(f'prompt deletion parameter invalid: {error_msgs}')
        return jsonify(dic), 400

    # 既存のデータの削除
    try:
        # prompt_idの最大revisionを取得するサブクエリを作成
        subquery = db.session.query(
            SystemPrompts.prompt_id,
            func.max(SystemPrompts.revision).label("max_revision")
        ).filter(SystemPrompts.prompt_id == prompt_id
        ).group_by(SystemPrompts.prompt_id).subquery()

        system_prompt = db.session.query(SystemPrompts).join(
            subquery, 
            db.and_(
                SystemPrompts.prompt_id == subquery.c.prompt_id,
                SystemPrompts.revision == subquery.c.max_revision
            )
        ).filter(
            SystemPrompts.is_deleted == False,
            SystemPrompts.revision == revision,
            SystemPrompts.updated_time == updated_time,
            db.or_(
                SystemPrompts.owner_user_no == current_user.user_no,
                SystemPrompts.is_editable_by_everyone == 1
            )
        ).first()

        if not system_prompt:
            # データはcurrent_userが変更できない状態である。
            error_msgs['main_error_message'] = '変更ができませんでした。'
            app_logger.warn(f'prompt deletion target not found: {data}')
            return jsonify(error_msgs), 400

        # 新しいrevisionで追加する。
        prompt = SystemPrompts(
                    prompt_id=prompt_id,
                    revision=int(revision) + 1,
                    prompt_name=system_prompt.prompt_name,
                    prompt_content=system_prompt.prompt_content, 
                    is_edit_locked=system_prompt.is_edit_locked,
                    is_viewable_by_everyone=system_prompt.is_viewable_by_everyone,
                    is_editable_by_everyone=system_prompt.is_editable_by_everyone,
                    owner_user_no=system_prompt.owner_user_no,
                    updated_user_no=current_user.user_no,
                    is_deleted=True,
                    updated_time=get_current_time())
        db.session.add(prompt)
        db.session.commit()

        return jsonify({'redirect': url_for('system_prompt_list', main_error_message='削除しました。')})
    except Exception as e:
        # エラーが発生した。
        app_logger.exception('システムプロンプトの削除に失敗しました。')
        error_msgs['main_error_message'] = 'エラーが発生しました。'
        return jsonify(error_msgs), 500
