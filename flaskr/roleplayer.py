from flask import session, render_template, request, url_for, jsonify
from . import app, db
from .models.system_prompts_db import Roleplayers
from .models.login_db import LoginUser
from sqlalchemy import func
from sqlalchemy.orm import aliased
from flask_login import login_required, current_user
from .utils.commons import is_empty, generate_random_string, is_numeric, get_current_time, checkbox_to_save, create_error_info, set_message_to_session, set_message_to_session
import json, logging

@app.route('/roleplayer/list', methods=['GET'])
@login_required
def roleplayer_list():

    # 受け渡されたメッセージを取得
    main_message, error_message = set_message_to_session('roleplayer', '_')

    # 閲覧ユーザのユーザ番号
    current_user_no = current_user.user_no

    # LoginUserテーブルのエイリアスを作成
    owner_user = aliased(LoginUser, name="owner_user")
    updated_user = aliased(LoginUser, name="updated_user")

    # 各prompt_idの最大revisionを取得するサブクエリを作成
    subquery = db.session.query(
        Roleplayers.roleplayer_id,
        func.max(Roleplayers.revision).label("max_revision")
    ).group_by(Roleplayers.roleplayer_id).subquery()

    roleplaylers = db.session.query(Roleplayers, owner_user.user_name, updated_user.user_name, 
                                      (Roleplayers.owner_user_no == current_user_no).label("is_owner")).join(
        subquery, 
        db.and_(
            Roleplayers.roleplayer_id == subquery.c.roleplayer_id,
            Roleplayers.revision == subquery.c.max_revision
        )
    ).outerjoin(
        owner_user,
        owner_user.user_no == Roleplayers.owner_user_no
    ).outerjoin(
        updated_user,
        updated_user.user_no == Roleplayers.updated_user_no
    ).filter(
        Roleplayers.is_deleted == False,
        db.or_(
            Roleplayers.owner_user_no == current_user_no,
            Roleplayers.is_viewable_by_everyone == True
        )
    ).order_by(Roleplayers.updated_time.desc()).all()

    return render_template("roleplayer_list.html", roleplaylers=roleplaylers, main_message=main_message, error_message=error_message)


@app.route('/roleplayer/', defaults={'roleplayer_id': None}, methods=['GET'])
@app.route('/roleplayer/<int:roleplayer_id>', methods=['GET'])
@login_required
def roleplayer_detail_show(roleplayer_id):

    csrf_token = generate_random_string(48)  # CSRF対策にランダムなシークレットキーを設定
    session['roleplayer_csrf_token'] = csrf_token

    if is_empty(roleplayer_id):
        # 新規登録
        return render_template("roleplayer.html", roleplayer={}, csrf_token=csrf_token)

    # 閲覧ユーザのユーザ番号
    current_user_no = current_user.user_no

    # 各prompt_idの最大revisionを取得するサブクエリを作成
    subquery = db.session.query(
        Roleplayers.roleplayer_id,
        func.max(Roleplayers.revision).label("max_revision")
    ).filter(Roleplayers.roleplayer_id == roleplayer_id
    ).group_by(Roleplayers.roleplayer_id).subquery()

    # LoginUserテーブルのエイリアスを作成
    owner_user = aliased(LoginUser, name="owner_user")
    updated_user = aliased(LoginUser, name="updated_user")

    roleplayer = db.session.query(Roleplayers, owner_user.user_name, updated_user.user_name, 
                                      (Roleplayers.owner_user_no == current_user_no).label("is_owner"),
                                      (db.or_(Roleplayers.owner_user_no == current_user_no, Roleplayers.is_editable_by_everyone == True)).label("is_editable")).join(
        subquery, 
        db.and_(
            Roleplayers.roleplayer_id == subquery.c.roleplayer_id,
            Roleplayers.revision == subquery.c.max_revision
        )
    ).outerjoin(
        owner_user,
        owner_user.user_no == Roleplayers.owner_user_no
    ).outerjoin(
        updated_user,
        updated_user.user_no == Roleplayers.updated_user_no
    ).filter(
        Roleplayers.is_deleted == False,
        db.or_(
            Roleplayers.owner_user_no == current_user_no,
            Roleplayers.is_viewable_by_everyone == True
        )
    ).order_by(Roleplayers.updated_time.desc()).first()

    if not roleplayer:
        # prompt_idが間違っている
        return render_template("roleplayer.html", main_error_message='指定したプロンプトが見つかりませんでした。', roleplayer={}, csrf_token=csrf_token), 404

    # シリアル化可能な形に変換
    roleplayer_data = {
        'roleplayer_id': roleplayer[0].roleplayer_id,
        'revision': roleplayer[0].revision,
        'roleplayer_name': roleplayer[0].roleplayer_name,
        'memo': roleplayer[0].memo,
        'prompt_id': roleplayer[0].prompt_id,
        'prompt_revision': roleplayer[0].prompt_revision,
        'is_edit_locked': roleplayer[0].is_edit_locked,
        'is_viewable_by_everyone': roleplayer[0].is_viewable_by_everyone,
        'is_editable_by_everyone': roleplayer[0].is_editable_by_everyone,
        'updated_time': roleplayer[0].updated_time
    }

    detail_data = {
        "Roleplayer": roleplayer_data,
        "owner_user": roleplayer[1],
        "updated_user": roleplayer[2],
        "is_owner": roleplayer[3],
        "is_editable": roleplayer[4]
    }
    roleplayer_json = json.dumps(detail_data, default=str)
    return render_template("roleplayer.html", roleplayer=detail_data, serialized_json=roleplayer_json, csrf_token=csrf_token)

@app.route('/roleplayer/', methods=['POST'])
@login_required
def roleplayer_detail():
    app_logger = logging.getLogger('app_logger')

    # パラメータを受け取る
    data = request.get_json()
    csrf_token = data['csrf_token']

    # CSRFトークンのチェック
    if not session['roleplayer_csrf_token'] == csrf_token:
        dic = {}
        dic['main_error_message'] = 'Invalid access.'
        return jsonify(dic), 403  # 不正なアクセス
    
    roleplayer_name = '' if not 'roleplayer_name' in data else data['roleplayer_name']
    memo = '' if not 'memo' in data else data['memo']
    is_edit_locked = '' if not 'is_edit_locked' in data else data['is_edit_locked']
    is_viewable_by_everyone = '' if not 'is_viewable_by_everyone' in data else data['is_viewable_by_everyone']
    is_editable_by_everyone = '' if not 'is_editable_by_everyone' in data else data['is_editable_by_everyone']
    roleplayer_id = '' if not 'roleplayer_id' in data else data['roleplayer_id']
    revision = '' if not 'revision' in data else data['revision']
    prompt_id = '' if not 'prompt_id' in data else data['prompt_id']
    prompt_revision = '' if not 'prompt_revision' in data else data['prompt_revision']
    updated_time = '' if not 'updated_time' in data else data['updated_time']

    # parameter check
    error_msgs = {}
    if not is_empty(roleplayer_id) and not is_numeric(roleplayer_id):
        error_msgs['roleplayer_id'] = 'Invalid roleplayer_id.'
    if len(roleplayer_name) < 1 or len(roleplayer_name) > 30:
        error_msgs['roleplayer_name'] = 'Invalid roleplayer name.'
    if not is_empty(is_edit_locked) and not is_numeric(is_edit_locked):
        error_msgs['main_error_message'] = 'Invalid access.'
    if not is_empty(is_viewable_by_everyone) and not is_numeric(is_viewable_by_everyone):
        error_msgs['main_error_message'] = 'Invalid access.'
    if not is_empty(is_editable_by_everyone) and not is_numeric(is_editable_by_everyone):
        error_msgs['main_error_message'] = 'Invalid access.'

    if not is_empty(prompt_id) and not is_numeric(prompt_id):
        error_msgs['main_error_message'] = 'Invalid access.'
    if not is_empty(prompt_revision) and not is_numeric(prompt_revision):
        error_msgs['main_error_message'] = 'Invalid access.'

    if error_msgs:
        return jsonify(dic), 400

    if roleplayer_id == '0' and revision == '0' and updated_time == '0':
        # 新規登録
        rs = db.session.query(
            func.max(Roleplayers.roleplayer_id).label('max_prompt_id')
        ).one_or_none()
        app_logger.debug(f'@@@@@@@@@@@ rs={rs}')
        roleplayer_id = 1
        if rs:
            roleplayer_id = roleplayer_id + rs[0]

        new_roleplayer = Roleplayers(
                    roleplayer_id=roleplayer_id,
                    revision=1,
                    roleplayer_name=roleplayer_name,
                    memo=memo, 
                    prompt_id=prompt_id,
                    prompt_revision=prompt_revision,
                    is_edit_locked=checkbox_to_save(is_edit_locked),
                    is_viewable_by_everyone=checkbox_to_save(is_viewable_by_everyone),
                    is_editable_by_everyone=checkbox_to_save(is_editable_by_everyone),
                    owner_user_no=current_user.user_no,
                    updated_user_no=current_user.user_no,
                    is_deleted=False,
                    updated_time=get_current_time())
        db.session.add(new_roleplayer)
        db.session.commit()

        set_message_to_session('roleplayer', id=roleplayer_id, message='登録しました。')
        return jsonify({'redirect': url_for('roleplayer_detail_show', roleplayer_id=roleplayer_id)})


    # 既存のデータを更新
    try:
        # prompt_idの最大revisionを取得するサブクエリを作成
        subquery = db.session.query(
            Roleplayers.roleplayer_id,
            func.max(Roleplayers.revision).label("max_revision")
        ).filter(Roleplayers.roleplayer_id == roleplayer_id
        ).group_by(Roleplayers.roleplayer_id).subquery()

        roleplayer = db.session.query(Roleplayers).join(
            subquery, 
            db.and_(
                Roleplayers.roleplayer_id == subquery.c.roleplayer_id,
                Roleplayers.revision == subquery.c.max_revision
            )
        ).filter(
            Roleplayers.is_deleted == False,
            Roleplayers.revision == revision,
            Roleplayers.updated_time == updated_time,
            db.or_(
                Roleplayers.owner_user_no == current_user.user_no,
                Roleplayers.is_editable_by_everyone == 1
            )
        ).first()

        if not roleplayer:
            # データはcurrent_userが変更できない状態である。
            response_code = 400
            error_msgs = create_error_info(message='変更ができませんでした。', status=response_code, path='/roleplayer/')
            return jsonify(error_msgs), response_code

        # 新しいrevisionで追加する。
        next_roleplayer = Roleplayers(
                    roleplayer_id=roleplayer_id,
                    revision=int(revision) + 1,
                    prompt_content=roleplayer, 
                    owner_user_no=roleplayer.owner_user_no,
                    updated_user_no=current_user.user_no,
                    is_deleted=False,
                    updated_time=get_current_time())

        if roleplayer.owner_user_no == current_user.user_no:
            # オーナーの場合に変更できる項目
            next_roleplayer.roleplayer_name = roleplayer_name
            next_roleplayer.memo = memo
            next_roleplayer.is_edit_locked = checkbox_to_save(is_edit_locked)
            next_roleplayer.is_viewable_by_everyone = checkbox_to_save(is_viewable_by_everyone)
            next_roleplayer.is_editable_by_everyone = checkbox_to_save(is_editable_by_everyone)

        db.session.add(next_roleplayer)
        db.session.commit()

        response_code = 200
        set_message_to_session('roleplayer', roleplayer_id, message='更新しました。', status = response_code)
        return jsonify({'redirect': url_for('roleplayer_detail_show', roleplayer_id=roleplayer_id)}), response_code

    except Exception as e:
        # エラーが発生した。
        response_code = 500
        message = 'システムプロンプトの更新に失敗しました。'
        app_logger.exception(message)
        error_info = create_error_info(message = message, status = response_code, path = '/roleplayer/')
        return jsonify(error_info), response_code

@app.route('/roleplayer/delete', methods=['POST'])
@login_required
def delete_prompt():
    app_logger = logging.getLogger('app_logger')

    # パラメータを受け取る
    data = request.get_json()
    csrf_token = data['csrf_token']

    # CSRFトークンのチェック
    if not session['roleplayer_csrf_token'] == csrf_token:
        response_code = 403
        message = 'Invalid access.'
        error_info = create_error_info(message = message, status = response_code, path = '/roleplayer/delete')
        return jsonify(error_info), response_code  # 不正なアクセス

    roleplayer_id = '' if not 'roleplayer_id' in data else data['roleplayer_id']
    revision = '' if not 'revision' in data else data['revision']
    updated_time = '' if not 'updated_time' in data else data['updated_time']

    # parameter check
    error_msgs = {}
    if not is_empty(roleplayer_id) and not is_numeric(roleplayer_id):
        error_msgs['roleplayer_id'] = 'Invalid roleplayer_id.'
    if not is_empty(revision) and not is_numeric(revision):
        error_msgs['revision'] = 'Invalid revision.'
    if not is_empty(updated_time) and not is_numeric(updated_time):
        error_msgs['updated_time'] = 'Invalid updated_time.'

    if error_msgs:
        response_code = 400
        message = 'Invalid parameters.'
        app_logger.warn(f'roleplayer deletion parameter invalid: {error_msgs}')
        error_info = create_error_info(message = message, status = response_code, path = '/roleplayer/delete', details = error_msgs)
        return jsonify(error_info), response_code

    # 既存のデータの削除
    try:
        # prompt_idの最大revisionを取得するサブクエリを作成
        subquery = db.session.query(
            Roleplayers.roleplayer_id,
            func.max(Roleplayers.revision).label("max_revision")
        ).filter(Roleplayers.roleplayer_id == roleplayer_id
        ).group_by(Roleplayers.roleplayer_id).subquery()

        roleplayer = db.session.query(Roleplayers).join(
            subquery, 
            db.and_(
                Roleplayers.roleplayer_id == subquery.c.roleplayer_id,
                Roleplayers.revision == subquery.c.max_revision
            )
        ).filter(
            Roleplayers.is_deleted == False,
            Roleplayers.revision == revision,
            Roleplayers.updated_time == updated_time,
            db.or_(
                Roleplayers.owner_user_no == current_user.user_no,
                Roleplayers.is_editable_by_everyone == 1
            )
        ).first()

        if not roleplayer:
            # データはcurrent_userが変更できない状態である。
            message = '変更ができませんでした。'
            response_code = 400
            error_info = create_error_info(message=message, path='/roleplayer/delete', status=response_code)
            app_logger.warn(f'roleplayer deletion target not found: {data}')
            return jsonify(error_info), response_code

        # 新しいrevisionで追加する。
        next_roleplayer = Roleplayers(
                    roleplayer_id=roleplayer_id,
                    revision=int(revision) + 1,
                    roleplayer_name=roleplayer.prompt_name,
                    memo=roleplayer.memo, 
                    prompt_id=roleplayer.prompt_id,
                    prompt_revision=roleplayer.prompt_revision,
                    is_edit_locked=roleplayer.is_edit_locked,
                    is_viewable_by_everyone=roleplayer.is_viewable_by_everyone,
                    is_editable_by_everyone=roleplayer.is_editable_by_everyone,
                    owner_user_no=roleplayer.owner_user_no,
                    updated_user_no=current_user.user_no,
                    is_deleted=True,
                    updated_time=get_current_time())
        db.session.add(next_roleplayer)
        db.session.commit()

        set_message_to_session('roleplayer', '_', message = '削除しました。')
        return jsonify({'redirect': url_for('roleplayer_list')})

    except Exception as e:
        # エラーが発生した。
        message = 'ロールプレイヤーの削除に失敗しました。'
        response_code = 500
        error_info = create_error_info(message=message, path='/roleplayer/delete', status=response_code, details=error_msgs)
        app_logger.exception(message)
        return jsonify(error_info), response_code
