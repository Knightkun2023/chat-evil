from flask import session, render_template, request, redirect, url_for, jsonify
from . import app
from .utils.commons import generate_random_string, get_query_param_from_url, create_error_info
from .utils.moderation_commons import check_moderation_main, get_moderation_result
import os

@app.route('/moderation/', methods=['GET'])
def system_prompt_detail_show_free():

    csrf_token = generate_random_string(48)  # CSRF対策にランダムなシークレットキーを設定
    session['moderation_csrf_token'] = csrf_token

    free_key = request.args.get('p', '')
    if free_key in app.config['MODERATION_CREDENTIALS']:
        return render_template("moderation.html", system_prompt={}, csrf_token=csrf_token,
                                user_name=app.config['MODERATION_CREDENTIALS'][free_key])

#    return render_template("error/403.html"), 403
    return redirect(url_for('login_show'))

@app.route('/moderation/check', methods=['POST'])
def check_moderation():

    # パラメータを受け取る
    data = request.get_json()
    authorized = False

    # CSRFトークンのチェック
    if 'csrf_token' in data:
        # CSRFトークンが渡された場合：
        csrf_token = data['csrf_token']
        if session['system_prompt_csrf_token'] == csrf_token:
            authorized = True

    if not authorized:
        # free_keyをチェックする
        custom_header_value = request.headers.get('X-Chat-Url', None)
        if custom_header_value:
            free_key = get_query_param_from_url(custom_header_value, 'p')
            if free_key in app.config['MODERATION_CREDENTIALS']:
                authorized = True

    if not authorized:
        response_code = 403
        # result_dict = {'error_message':'Error', 'result': []}
        result_dict = create_error_info(message='Forbidden.', status=response_code, path='/moderation/check')
        return jsonify(result_dict), response_code

    content = data['content']
    moderation_model_no = 1
    if data['moderation_model_no'] == '2':
        moderation_model_no = 2
    result_dict = get_moderation_result(content=content, key=os.environ['OPENAI_API_KEY'], moderation_model_no=moderation_model_no)

    response_code = 200
    if 'error' in result_dict:
        # エラーだった場合
        response_code = 400
        # dic = {'error_message':'Error', 'result': result_dict}
        # result_dict = dic
        result_dict = create_error_info(message = 'Error occurred.', status = response_code, path = '/moderation/check', details=result_dict)

    return jsonify(result_dict), response_code

@app.route('/moderation/check-for-chat', methods=['POST'])
def check_moderation_for_chat():

    # free_keyをチェックする
    custom_header_value = request.headers.get('X-Chat-Url', None)
    if custom_header_value and not custom_header_value.startswith(app.config['REMOTE_URL']):
        response_code = 403
        # result_dict = {'error_message':'Error', 'result': []}
        result_dict = create_error_info(message = 'Forbidden.', status = response_code, path = '/moderation/check-for-chat')
        return jsonify(result_dict), response_code

    # パラメータを受け取る
    data = request.get_json()
    content = data.get('content', '')
    moderation_model_no = 1
    if data.get('moderation_model_no') == '2':
        moderation_model_no = 2

    content = content.strip()
    if content == '':
        return jsonify(create_error_info(message='Empty content.', status = 404, path = '/moderation/check2'))

    result, status_code = check_moderation_main(content, moderation_model_no)
    return jsonify(result), status_code

@app.route('/moderation/check2', methods=['POST'])
def check_moderation2():

    # free_keyをチェックする
    custom_header_value = request.headers.get('X-Chat-Url', None)
    if custom_header_value and not custom_header_value.startswith('https://chat.openai.com/'):
        response_code = 403
        # result_dict = {'error_message':'Error', 'result': []}
        result_dict = create_error_info(message = 'Forbidden.', status = response_code, path = '/moderation/check2')
        return jsonify(result_dict), response_code

    # パラメータを受け取る
    data = request.get_json()
    content = data.get('content', '')
    moderation_model_no = 1
    if data.get('moderation_model_no') == '2':
        moderation_model_no = 2

    content = content.strip()
    if content == '':
        return jsonify(create_error_info(message='Empty content.', status = 404, path = '/moderation/check2'))

    result, status_code = check_moderation_main(content, moderation_model_no)
    return jsonify(result), status_code
