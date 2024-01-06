from flask import session, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_session import Session
import os
from . import app, db
from .models.login_db import LoginUser, RegistrationCode, LoginHistory
from datetime import datetime, timedelta
from .utils.commons import is_empty, valid_datetime, is_numeric, get_current_time, generate_random_string, is_alpha_digits, get_display_time
from sqlalchemy.sql import func

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_show'
Session(app)

@app.route('/login', methods=['GET'])
def login_show():
    login_id = session.pop('login_id', '')
    if not is_empty(request.args.get('login_id', '')):
        login_id = request.args.get('login_id', '')
    csrf_token = generate_random_string(48)  # CSRF対策にランダムなシークレットキーを設定
    session['login_csrf_token'] = csrf_token
    return render_template(
        'login.html', login_id=login_id, csrf_token=csrf_token
    )

@app.route('/login', methods=['POST'])
def login_process():

    data = request.get_json()
    user_id = data['login_id']
    password = data['password']
    csrf_token = data['csrf_token']

    # CSRFトークンのチェック
    if not 'login_csrf_token' in session or not session['login_csrf_token'] == csrf_token:
        # CSRF token is not valid, show an error message or redirect
        return jsonify({'main_error_message': 'Invalid username or password'}), 401  # ログイン失敗

    user = LoginUser.query.filter_by(user_id=user_id).order_by(LoginUser.revision.desc()).first()

    if user is not None and user.check_password(password):
        login_user(user)

        # ログイン成功時の履歴を保存
        login_history = LoginHistory(
            user_no=user.user_no,
            user_id=user.user_id,
            login_time=get_current_time(),
            user_agent=request.headers.get('User-Agent'),
            remote_ip=request.remote_addr,
            is_success=True
        )
        db.session.add(login_history)
        db.session.commit()

        return jsonify({'redirect': url_for('index')})

    # ログイン失敗時の履歴を保存
    login_history = LoginHistory(
        user_no=None,
        user_id=user_id[:30],
        login_time=get_current_time(),
        user_agent=request.headers.get('User-Agent'),
        remote_ip=request.remote_addr,
        is_success=False
    )
    db.session.add(login_history)
    db.session.commit()

    return jsonify({'main_error_message': 'Invalid username or password'}), 401  # ログイン失敗

@app.route('/logout')
def logout_process():
    session['login_id'] = current_user.user_id
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    user_no, revision = user_id.split('#')
    return LoginUser.query.filter_by(user_no=int(user_no), revision=int(revision)).first()

@app.route('/registration_code_list', methods=['GET'])
@login_required
def get_registration_code_list():

    # 管理者権限があるかチェック
    has_admin_role()

    current_time = get_current_time()
    registration_codes = db.session.query(
        RegistrationCode.registration_code,
        RegistrationCode.remarks,
        RegistrationCode.is_used,
#        LoginUser.user_id,
        RegistrationCode.issuing_time,
        RegistrationCode.expiration_time,
        RegistrationCode.roles
#    ).join(LoginUser, LoginUser.user_no == RegistrationCode.issuing_user_no).filter(
    ).filter(
        RegistrationCode.is_deleted == False,
        RegistrationCode.expiration_time > current_time
    ).order_by(RegistrationCode.issuing_time.desc()).all()

    return render_template("registration_code_list.html", registration_codes=registration_codes)

@app.route('/registration_code', methods=['GET', 'POST'])
@login_required
def create_registration_code():

    # 管理者権限があるかチェック
    has_admin_role()

    if request.method == 'GET':
        csrf_token = generate_random_string(48)  # CSRF対策にランダムなシークレットキーを設定
        session['registration_code_csrf_token'] = csrf_token
        return render_template('registration_code.html', csrf_token=csrf_token)

    data = request.get_json()
    csrf_token = data['csrf_token']

    # CSRFトークンのチェック
    if not session['registration_code_csrf_token'] == csrf_token:
        # CSRF token is not valid, show an error message or redirect
        return jsonify({'registration_code': 'Invalid access.'}), 403  # 不正なアクセス

    # パラメータを受け取る
    registration_code = data['registration_code']
    remarks = data['remarks']
    expiration_time = data['expiration_time']
    roles = data['roles']    

    error_msgs = {}
    if not is_empty(registration_code) and len(registration_code) > 64:
        error_msgs['registration_code'] = 'registration code is too long.'
    if is_empty(remarks):
        error_msgs['remarks'] = 'remarks is required.'
    elif len(remarks) > 128:
        error_msgs['remarks'] = 'remarks is too long.'
    if not is_empty(expiration_time):
        if len(expiration_time) > 17:
            error_msgs['expiration_time'] = 'expiration time is too long.'
        elif not valid_datetime(expiration_time):
            error_msgs['expiration_time'] = 'expiration time is not date time format(yyyyMMddHHmmssSSS).'
    if is_empty(roles) or not is_numeric(roles):
        error_msgs['roles'] = 'roles is not a number.'

    if error_msgs:
        return jsonify(error_msgs), 400  # 入力チェックエラー

    if is_empty(registration_code):
        registration_code=generate_random_string(48)

    if is_empty(expiration_time):
        # 現在の日時を取得
        now = datetime.now()
        # 3日間の分数を現在の日時に加える
        future_date = now + timedelta(minutes=app.config['EXPIRATION_MINUTES'])
        # 新しい日時を指定した形式にフォーマット
        expiration_time = future_date.strftime('%Y%m%d%H%M%S%f')[:17]
    else:
        expiration_time = expiration_time + '000000000'
        expiration_time = expiration_time[:17]

    # 登録コードを登録
    registration_code_record = RegistrationCode(
        registration_code=registration_code,
        remarks=remarks,
        is_used=0,
#        issuing_user_no=current_user.user_no,
        issuing_user_no=0,
        issuing_time=get_current_time(),
        expiration_time=expiration_time,
        register_time=None,
        registered_user_no=None,
        is_deleted=0,
        deleted_time=None,
        roles=roles
    )
    db.session.add(registration_code_record)
    db.session.commit()

    return jsonify({'redirect': url_for('get_registration_code_list')})

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'GET':
        registration_code = request.args.get('r')
        if is_empty(registration_code):
            registration_code = generate_random_string(52)  # 存在しない登録コードを設定
        csrf_token = generate_random_string(48)  # CSRF対策にランダムなシークレットキーを設定
        session['register_user_csrf_token'] = csrf_token
        session['registration_code'] = registration_code
        return render_template('register_user.html', csrf_token=csrf_token)

    # パラメータを受け取る
    data = request.get_json()
    csrf_token = data['csrf_token']

    # 登録コードを確認
    current_time = get_current_time()
    rs_registration_codes = RegistrationCode.query.filter(
        RegistrationCode.registration_code == session['registration_code'],
        RegistrationCode.is_used == False,
        RegistrationCode.is_deleted == False,
        RegistrationCode.expiration_time > current_time
    ).order_by(RegistrationCode.issuing_time.desc()).first()

    # 登録コードおよびCSRFトークンのチェック
    if not rs_registration_codes or not session['register_user_csrf_token'] == csrf_token:
        dic = {}
        dic['main_error_message'] = 'Invalid access.'
        dic['login_id'] = 'Invalid access.'
        return jsonify(dic), 403  # 不正なアクセス
    
    # パラメータチェック
    login_id = data['login_id']
    password = data['password']
    user_name = data['user_name']

    error_msgs = {}
    if not is_alpha_digits(login_id, 0, 30, True):
        error_msgs['login_id'] = 'Invalid login id.'
    if is_empty(password) or len(password) < 8:
        error_msgs['password'] = 'Invalid password.'
    if is_empty(user_name) or len(user_name) > 30:
        error_msgs['user_name'] = 'Invalid user_name.'

    if not 'login_id' in error_msgs:
        rs_login_user = LoginUser.query.filter(
            LoginUser.user_id == login_id
        ).first()
        if rs_login_user:
            error_msgs['login_id'] = 'Duplicated login id.'

    if error_msgs:
        error_msgs['main_error_message'] = '入力エラーがあります。ご確認ください。'
        return jsonify(error_msgs), 400  # 入力チェックエラー

    # ログインユーザの登録
    rs = db.session.query(
        func.max(LoginUser.user_no).label('max_user_no')
    ).one_or_none()
    user_no = 1
    if not rs:
        user_no = user_no + rs.max_user_no

    app_logger.debug(f'@@@@@@@@@@ login_id={login_id}')
    user = LoginUser(user_no=user_no, revision=1, user_id=login_id, user_name=user_name, 
                     roles=rs_registration_codes.roles, updated_time=get_current_time())
    user.set_password(password)
    db.session.add(user)

    # 登録キーを使用済みに変更
    registration_codes_record = rs_registration_codes
    registration_codes_record.is_used = True
    registration_codes_record.register_time = get_current_time()
    registration_codes_record.registered_user_no = user_no
    db.session.add(registration_codes_record)
    db.session.commit()

    login_user(user)

    return jsonify({'redirect': url_for('index')})

def has_admin_role() -> None:
    # 管理者権限があるかチェック
    if not current_user.roles & 1:
        logout_user()
        return redirect(url_for('login_show'))
