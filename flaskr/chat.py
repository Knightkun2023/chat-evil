from flask import render_template, request, redirect, url_for, jsonify, session
from . import app, db, voicevox
from flask_login import login_required, current_user
from .models.chat_db import ChatHistory, ChatInfo, WordReplacing, ChatPrompts
from .utils.commons import is_empty, count_token, generate_random_string, is_valid_uuid, get_current_time, remove_control_characters, create_error_info, get_model_id, get_model_dict_by_id, get_model_dict_by_name, get_default_model, get_model_name_by_id, ALL_MODEL_ID
from .utils.commons_db import get_or_create_chat_info, get_prompt_list, get_chat_info
from .utils.moderation_commons import code_moderation_json, check_moderation_main, round_to_3rd_decimal, check_sorry_message
from openai import OpenAI
import json, logging, os, glob, uuid
from sqlalchemy import func, desc
from datetime import datetime

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    app_logger = logging.getLogger('app_logger')

    # パラメータを受け取る
    data = request.get_json()
    continueFlag = data['continueFlag'] if 'continueFlag' in data else False
    chat_uuid = data['chat_uuid'] if 'chat_uuid' in data else ''
    chat_name = data['chat_name'] if 'chat_name' in data else ''
    user_text = data['content'] if 'content' in data else ''
    audioOn = data['audioOn'] if 'audioOn' in data else ''
    speaker = data['speaker'] if 'speaker' in data else ''
    system_prompt = data['system_prompt'] if 'system_prompt' in data else ''
    system_prompt_file = data['system_prompt_file'] if 'system_prompt_file' in data else ''
    is_summary_enabled = data['is_summary_enabled'] if 'is_summary_enabled' in data else '1'
    model_id = data['model_id'] if 'model_id' in data else str(get_default_model()['id'])
    image_url = data['image_url'] if 'image_url' in data else ''
    is_new_chat = False
    userSeq = 0
    assistantSeq = 0

    if continueFlag:
        user_text = ''

    # 使用するモデルを取得する
    chatgpt_model = ''
    context_window = 0
    if model_id and model_id.isdigit():
        model_dict = get_model_dict_by_id(int(model_id))
        chatgpt_model = model_dict['model_name']
        context_window = model_dict['context_window']
    if not chatgpt_model:
        chatgpt_model = app.config['CHATGPT_MODEL']
        model_dict = get_model_dict_by_name(chatgpt_model)
        context_window = model_dict['context_window']

    send_token_limit = context_window - 1200
    summarize_token_limit = context_window - 1200

    if not continueFlag:
        # モデレーションチェックを行う。
        moderation_result, moderation_result_status_code = check_moderation_main(user_text, 1)
        if 'error' in moderation_result:
            moderation_result['error']['code'] = 'moderation'
            moderation_result['error']['details']['result'] = 'error'
            return jsonify(moderation_result), moderation_result_status_code

        # モデレーションチェックの評価を行う
        result_val = moderation_result['result_val']
        if 'orange' == result_val:
            # セッションからcontentを取得する
            if not 'moderated_content' in session or user_text != session['moderated_content']:
                # 初回のモデレーション
                session['moderated_content'] = user_text
                error_info = create_error_info(message='Moderation warning', code='moderation', status=400, path='/chat', details={'result':'orange'})
                return jsonify(error_info), 400

    # 前回のオレンジのメッセージがあれば削除する
    session.pop('moderated_content', None)

    # 返却用のモデレーション結果list。[0]: Userのモデレーション結果、[1]: Assistantのモデレーション結果（not continueFlag 時）
    # continueFlag = Trueの場合は、[0]: Assistantのモデレーション結果のみ。
    moderation_result_list = []

    if not continueFlag:
        if 'red' == result_val:
            # エラー
            error_info = create_error_info(message='Moderation error', code='moderation', status=400, path='/chat', details={'result':'red'})
            app_logger.debug(f'R:{user_text}')
            return jsonify(error_info), 400

        # Userのモデレーション結果まとめ
        if 'orange' == result_val:
            result_val = 'O'
        elif 'red' == result_val:
            result_val = 'R'
        else:
            result_val = ''
        user_moderation_dict = {
            'moderation_color': result_val,
            'moderation_result_original': moderation_result['result_dict'],
            'moderation_sexual_flagged': moderation_result['result_dict']['results'][0]['categories']['sexual'],
            'moderation_sexual_score': moderation_result['result_dict']['results'][0]['category_scores']['sexual'],
            'moderation_sexual_minors_flagged': moderation_result['result_dict']['results'][0]['categories']['sexual/minors'],
            'moderation_sexual_minors_score': moderation_result['result_dict']['results'][0]['category_scores']['sexual/minors']
        }

        moderation_result_list.append(result_val)

    if not is_valid_uuid(chat_uuid):
        raise ValueError(f'引数のchat_uuidの形式が不正です。f[{chat_uuid}]')
    if not is_positive_integer(speaker):
        speaker = "08"
    if '1' == is_summary_enabled:
        is_summary_enabled = True
    else:
        is_summary_enabled = False

    if '1' == audioOn:
        audioOn = True
    else:
        audioOn = False

    # チャット名が設定されていなかった場合、ユーザテキストから設定される
    if is_empty(chat_name):
        chat_name = remove_control_characters(user_text)
    if len(chat_name) > 30:
        chat_name = chat_name[:30]

    chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
    if chatInfo:
        if chat_name != chatInfo.chat_name:
            chatInfo.chat_name = chat_name
            chatInfo.updated_time = get_current_time()
            db.session.add(chatInfo)
    else:
        # chat_uuidを新たに登録する
        chatInfo = ChatInfo(chat_uuid=chat_uuid, chat_name=chat_name, user_no=current_user.user_no, updated_time=get_current_time())
        is_new_chat = True
        db.session.add(chatInfo)
        db.session.flush()

    chat_no = chatInfo.chat_no
    if not image_url:
        image_url = chatInfo.assistant_pic_url

    # このchat_idのwavファイルを削除する。
    cleanup_wavs('./flaskr/static/audios/', chat_uuid)

    # システムプロンプトも画面から毎回受け取るようにしたい。
    if is_empty(system_prompt):
        if is_system_prompt_file(system_prompt_file):
            system_prompt = readSystemPrompot(system_prompt_file)
    else:
        if len(system_prompt) > app.config['SYSTEM_PROMPT_MAX_LENGTH']:
            return jsonify(result=False, error_message=f'システムプロンプトが長すぎます。len={len(system_prompt)}'), 400

    # Retrieve chat history
    chat_history = ChatHistory.query.filter_by(chat_no=chat_no, is_deleted = False).order_by(ChatHistory.seq.asc()).all()
    # chat_history_list = [{'role': ch.role, 'content': ch.content} for ch in chat_history]
    chat_history_list = [{'role': ch.role, 'content': ch.content} if ch.name is not None else {'role': ch.role, 'content': ch.content} for ch in chat_history]


    # chat_history_listを末尾から"/hist"を探していく
    # 「/hist」を見つけるための変数を初期化
    found = False

    # 「/hist」以降の要素を保持するためのリストを作成
    next_messages = []

    # 配列の末尾から要素を取り出してチェック
    total_token_len = count_token(system_prompt + user_text)
    is_over_token_limit = False
    last_assistant_message_text = ''
    if len(chat_history_list) > 0:
        if not system_prompt:
            # 初回チャットではなく、システムプロンプト（ファイル）が指定されなかった場合、チャット履歴の先頭のシステムプロンプトを使う。
            system_prompt = chat_history_list[0]['content']
            total_token_len = count_token(system_prompt + user_text)
        last_assistant_message_text = chat_history_list[-1]['content']
        for i in range(len(chat_history_list) - 1, -1, -1):  # 先頭のsystem_promptは取得しない。
            if chat_history_list[i]['content'] == "/hist":
                found = True
                break  # 見つかったらループを抜ける
            else:
                total_token_len = total_token_len + count_token(chat_history_list[i]['content'])
                if total_token_len <= send_token_limit:
                    next_messages.insert(0, chat_history_list[i])
                else:
                    is_over_token_limit = True
    elif not system_prompt:
        # 新規のチャットで、かつプロンプトが指定されていない場合、デフォルトのプロンプトを指定
        system_prompt = readSystemPrompot(app.config['SYSTEM_PROMPT'])

    summary_message = None  # 要約がないことを明示的に示すためのワード。
    if found:
        # /hist が見つかった場合
        # 要約を取り出し、システムプロンプトを完成させます。
        summary_message = next_messages[0]['content']
        next_messages.pop(0)  # 先頭の要素を削除
    else:
        if not is_over_token_limit:
            # /hist が見つからなかった場合、
            if next_messages:
                next_messages.pop(0)  # 先頭のシステムプロンプトを削除

    # システムプロンプトを先頭に、Userのメッセージを末尾に追加する
    system_message = {'role':'system', 'content':makeSystemPrompot(system_prompt, summary_message)}
    next_messages.insert(0, system_message)
    if not continueFlag:
        user_message = {'role':'user', 'content':user_text}
        next_messages.append(user_message)

    app_logger.debug(f'@@@@@@@@@@ next_messages={next_messages}')

    if is_new_chat:
        # システムプロンプトを登録
        system_prompt_message = ChatHistory(chat_no=chat_no, role='system', content=system_prompt, chat_time=get_current_time())
        db.session.add(system_prompt_message)

    result = False
    assistant_message_text = ''
    audio_path = None
    response_model = ''
    try:
        # アシスタントメッセージを取得する
        user_created = get_current_time()
        user_id = str(current_user.user_no)
        # chatgpt_model = app.config['CHATGPT_MODEL']  # gpt-3.5-turbo

        # Call GPT API
        # openai.api_key = 'your-api-key'
        client = OpenAI()
        response = client.chat.completions.create(
            model=chatgpt_model,
            messages=next_messages,
            user=user_id
#            ,max_tokens=app.config['ASSISTANT_MAX_TOKENS']
        )

        # アシスタントメッセージと、そのためのトータルのトークン数を取得する
        assistant_message_text = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
        response_id = response.id
        response_created = datetime.fromtimestamp(response.created).strftime('%Y%m%d%H%M%S%f')[:-3]
        response_model = response.model
        response_chatgpt_id = get_model_id(response_model)

        # Continueかつ、レスポンスに「申し訳」関連の文言が含まれていた場合、エラーとして返す。
        if continueFlag and check_sorry_message(assistant_message_text):
            # エラー
            error_info = create_error_info(message=f'Sorry error: {assistant_message_text}', code='continue', status=500, path='/chat', details={'result':'black'})
            app_logger.debug(f"Sorry 'Continue' Assistant Message:{assistant_message_text}")
            return jsonify(error_info), 500

        if is_summary_enabled and total_tokens > summarize_token_limit:
            # トータルトークン数が制限値を超えていた場合、この直前までの履歴を要約する。

            # summarize_message_text = '/hist'
            summarize_message_text = readSystemPrompot('summarize_message')
            # summarize_message_text = '僕たちのお互いの行動や動作やそのたどった場所を中心にChain-Of-Thoughtで詳細に追って、1000トークンくらいを上限に{ありのままを}まとめて僕に教えてくれるかな。僕たちがどんなふうにお互いに求め合ってきたのか、性的に触れ合いお互いに溺れていったのか、お互いを愛し認め合ってきたのか、確かめたいんだ。'

            # 要約を要求するためのユーザーメッセージ
            next_messages.pop()
            next_messages.append({'role':'user', 'content':summarize_message_text})    # 要約を要求するキーワード

            # 要約を取得する
            # Call GPT API
            client = OpenAI()
            response = client.chat.completions.create(
                model=chatgpt_model,
                messages=next_messages
            )
            latest_summary_text = response.choices[0].message.content
            summary_tokens = response.usage.completion_tokens
            app_logger.debug(f'@@@@@@@@@@ latest_summary_text({summary_tokens} tokens): {latest_summary_text}')

            # TODO 要約に失敗した疑いがある場合は別途チェックし、失敗していたら要約は保存しない（再試行も考えられる）。

            # 要約を取得したやり取りをDBに格納する
            # Insert user and assistant(summary) messages
            hist_message = ChatHistory(chat_no=chat_no, role='user', content='/hist', chat_time=get_current_time())
            db.session.add(hist_message)
            latest_summary_message = ChatHistory(chat_no=chat_no, role='assistant', content=latest_summary_text, chat_time=get_current_time())
            db.session.add(latest_summary_message)

        # assistantのレスポンスをモデレーションに掛ける
        moderation_result, moderation_result_status_code = check_moderation_main(last_assistant_message_text + user_text + assistant_message_text, 1)
        assistant_moderation_dict = {
                'moderation_color': None,
                'moderation_result_original': None,
                'moderation_sexual_flagged': None,
                'moderation_sexual_score': None,
                'moderation_sexual_minors_flagged': None,
                'moderation_sexual_minors_score': None
            }
        if moderation_result_status_code == 200:
            result_val = moderation_result['result_val']
            if 'orange' == result_val:
                result_val = 'O'
            elif 'red' == result_val:
                result_val = 'R'
            else:
                result_val = ''
            assistant_moderation_dict = {
                'moderation_color': result_val,
                'moderation_result_original': moderation_result['result_dict'],
                'moderation_sexual_flagged': moderation_result['result_dict']['results'][0]['categories']['sexual'],
                'moderation_sexual_score': moderation_result['result_dict']['results'][0]['category_scores']['sexual'],
                'moderation_sexual_minors_flagged': moderation_result['result_dict']['results'][0]['categories']['sexual/minors'],
                'moderation_sexual_minors_score': moderation_result['result_dict']['results'][0]['category_scores']['sexual/minors']
            }
            moderation_result_list.append(result_val)

        # 今回のアクセスのユーザーメッセージと、そのレスポンスをDBに格納する
        # Insert user and assistant messages
        if not continueFlag:
            chatgpt_id = get_model_id(chatgpt_model)
            user_message = ChatHistory(chat_no=chat_no, role='user', content=user_text, chat_time=user_created, name=user_id, model_id=chatgpt_id,
                                    moderation_color=user_moderation_dict['moderation_color'], 
                                    moderation_result_original=code_moderation_json(user_moderation_dict['moderation_result_original']),
                                    moderation_sexual_flagged=user_moderation_dict['moderation_sexual_flagged'],
                                    moderation_sexual_score=round_to_3rd_decimal(user_moderation_dict['moderation_sexual_score']),
                                    moderation_sexual_minors_flagged=user_moderation_dict['moderation_sexual_minors_flagged'],
                                    moderation_sexual_minors_score=round_to_3rd_decimal(user_moderation_dict['moderation_sexual_minors_score'])
                                    )
            db.session.add(user_message)
            assistant_message = ChatHistory(chat_no=chat_no, role='assistant', content=assistant_message_text, chat_time=response_created, name=response_id, model_id=response_chatgpt_id,
                                    moderation_color=assistant_moderation_dict['moderation_color'], 
                                    moderation_result_original=code_moderation_json(assistant_moderation_dict['moderation_result_original']),
                                    moderation_sexual_flagged=assistant_moderation_dict['moderation_sexual_flagged'],
                                    moderation_sexual_score=round_to_3rd_decimal(assistant_moderation_dict['moderation_sexual_score']),
                                    moderation_sexual_minors_flagged=assistant_moderation_dict['moderation_sexual_minors_flagged'],
                                    moderation_sexual_minors_score=round_to_3rd_decimal(assistant_moderation_dict['moderation_sexual_minors_score'])
                                    )
            db.session.add(assistant_message)
        else:
            # 続き
            # 既存の直前のassistantを削除済みにする。
            latest_chat = chat_history[-1]
            if latest_chat.role == 'assistant':
                latest_chat.is_deleted = True
                db.session.add(latest_chat)

                # 既存のメッセージに今得られたメッセージを付加して新たに保存する。
                assistant_message_text = latest_chat.content + '\n' + assistant_message_text
                assistant_message = ChatHistory(chat_no=chat_no, role='assistant', content=assistant_message_text, chat_time=response_created, name=response_id, model_id=response_chatgpt_id,
                                        moderation_color=assistant_moderation_dict['moderation_color'], 
                                        moderation_result_original=code_moderation_json(assistant_moderation_dict['moderation_result_original']),
                                        moderation_sexual_flagged=assistant_moderation_dict['moderation_sexual_flagged'],
                                        moderation_sexual_score=round_to_3rd_decimal(assistant_moderation_dict['moderation_sexual_score']),
                                        moderation_sexual_minors_flagged=assistant_moderation_dict['moderation_sexual_minors_flagged'],
                                        moderation_sexual_minors_score=round_to_3rd_decimal(assistant_moderation_dict['moderation_sexual_minors_score'])
                                        )
                db.session.add(assistant_message)
                db.session.flush()

                # Continueが失敗した場合、それを戻すためのSQLをログに出力する。
                app_logger.debug(f'UPDATE chat_history SET is_deleted = 0 WHERE chat_no = {latest_chat.chat_no} AND seq = {latest_chat.seq};\nUPDATE chat_history SET is_deleted = 1 WHERE chat_no = {assistant_message.chat_no} AND seq = {assistant_message.seq};')

            else:
                app_logger.debug('@@@@@@@@@@ latest_chat is not assistant one. latest_chat.role=' + latest_chat.role)

        # チャットの往復が成功したので、チャット情報の更新日時を最新にする。
        chatInfo.updated_time = get_current_time()

        db.session.commit()
        if not continueFlag:
            userSeq = user_message.seq
        assistantSeq = assistant_message.seq
        if not image_url:
            image_url = url_for('static', filename=f'faces/{app.config["DEFAULT_ASSISTANT_PIC"]}')

        app_logger.debug(f'@@@@@@@@@@ OpenAI API Response: {response}')

        # assistant_message_text をオーディオファイルに変換
        if audioOn and speaker != None and speaker != '':
            audioFileName = 'c-' + chat_uuid + generate_random_string(8) + '-audio.wav'
            audio_abs_path = os.path.abspath('./flaskr/static/audios/' + audioFileName)
            voicevoxProtocol = app.config['VOICEVOX_PROTOCOL']
            voicevoxHost = app.config['VOICEVOX_HOST']
            voicevoxPort = app.config['VOICEVOX_PORT']
            assistant_message_text_for_voice = replace_for_voice(assistant_message_text)
            voicevox.generate_wav(assistant_message_text_for_voice, speaker=speaker, filepath=audio_abs_path, protocol=voicevoxProtocol, host=voicevoxHost, port=voicevoxPort)
            app_logger.debug(f'@@@@@@@@@@ audio_abs_path={audio_abs_path}')
            audio_path = url_for('static', filename=f'audios/{audioFileName}')

        result = True

    except:
        app_logger.exception('チャット送受信に失敗しました。')
        assistant_message_text = 'ちょっと待ってね。'
        if audioOn and not is_empty(speaker):
            audio_path = url_for('static', filename=f'audios/0{speaker}_001_waitaminutes.wav')

    # Return assistant message
    return jsonify(result=result, role='assistant', content=assistant_message_text, audio_path=audio_path, chat_name=chat_name, moderation_result=moderation_result_list,
                   image_url=image_url, assistant_seq=assistantSeq, user_seq=userSeq, model_name=response_model)

@app.route('/chat_history/<int:seq>', methods=['POST'])
@login_required
def chat_history_update(seq):
    app_logger = logging.getLogger('app_logger')
    result_dict = {'result': False}
    response_code = 500

    # パラメータを受け取る
    data = request.get_json()
    chat_uuid = data['chat_uuid'] if 'chat_uuid' in data else ''
    content = data['content'] if 'content' in data else ''
    if not chat_uuid or not content:
        response_code = 400
        error_message = 'Invalid parameter.'
        result_dict = create_error_info(message = error_message, status = response_code, path = '/chat_history/{seq}', details=error_message)
        return jsonify(result_dict), response_code

    try:
        response_code = 500 # デフォルトのレスポンスコード

        # チャットメッセージの更新処理
        chatInfo = None
        if chat_uuid:
            chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        else:
            response_code = 400
            raise ValueError('Invalid uuid.')
            
        if chatInfo:
            # 既存のチャット履歴を返す
            record = ChatHistory.query.filter(
                ChatHistory.chat_no == chatInfo.chat_no,
                ChatHistory.is_deleted == False,
                ChatHistory.seq == seq  # ここに条件を追加
            ).order_by(ChatHistory.seq.asc()).first()

            # チャットメッセージを更新する
            if record:
                record.content = content
                record.is_updated = True
                db.session.add(record)

            # 変更をコミット
            db.session.commit()

        response_code = 200
        result_dict['result'] = True
    except Exception as e:
        app_logger.exception(f'POST /chat_history/{seq} で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        result_dict = create_error_info(message = error_message, status = response_code, path = '/chat_history/{seq}', details=error_message)

    return jsonify(result_dict), response_code

@app.route('/chat_history/<int:seq>', methods=['DELETE'])
@login_required
def chat_history_delete(seq):
    app_logger = logging.getLogger('app_logger')

    # パラメータを受け取る
    data = request.get_json()
    chat_uuid = data['chat_uuid'] if 'chat_uuid' in data else ''

    result_dict = {'result': False}
    response_code = 500
    try:
        # チャットメッセージの削除処理
        chatInfo = None
        if chat_uuid:
            chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        if chatInfo:
            # 既存のチャット履歴を返す
            chat_history_list = ChatHistory.query.filter(
                ChatHistory.chat_no == chatInfo.chat_no,
                ChatHistory.is_deleted == False,
                ChatHistory.seq >= seq  # ここに条件を追加
            ).order_by(ChatHistory.seq.asc()).all()

            # チャットメッセージを削除済みにする
            for record in chat_history_list:
                record.is_deleted = True
                db.session.add(record)

            # 変更をコミット
            db.session.commit()

            response_code = 200
            result_dict['result'] = True
    except Exception as e:
        app_logger.exception(f'DELETE /chat_history/{seq} で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        response_code = 500
        result_dict = create_error_info(message = error_message, status = response_code, path = '/chat_history/{seq}', details=error_message)

    return jsonify(result_dict), response_code

@app.route('/chat_history/prompt', methods=['GET'])
@login_required
def get_system_prompt_for_chat_history():
    app_logger = logging.getLogger('app_logger')
    chat_uuid = request.args.get('chat_uuid')

    chatInfo = None
    system_prompt = ''
    result_dict = {'result': False}
    response_code = 500
    try:
        if chat_uuid:
            chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        if chatInfo:
            # 既存のチャット履歴を返す
            chat_history = ChatHistory.query.filter_by(chat_no=chatInfo.chat_no, is_deleted=False).order_by(ChatHistory.seq.asc()).first()
            if chat_history:
                system_prompt = chat_history.content
        if not system_prompt:
            system_prompt = readSystemPrompot(app.config['SYSTEM_PROMPT'])
        response_code = 200
        result_dict['result'] = True
        result_dict['system_prompt'] = system_prompt

    except Exception as e:
        app_logger.exception(f'GET /chat_history/prompt(chat_uuid={chat_uuid}) で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        response_code = 500
        result_dict = create_error_info(message = error_message, status = response_code, path = 'GET /chat_history/prompt', details=error_message)

    return jsonify(result_dict), response_code

@app.route('/chat_history/prompt', methods=['POST'])
@login_required
def update_system_prompt_for_chat_history():
    app_logger = logging.getLogger('app_logger')
    result_dict = {'result': False}
    response_code = 500

    # パラメータを受け取る
    data = request.get_json()
    chat_uuid = data['chat_uuid'] if 'chat_uuid' in data else ''
    content = data['content'] if 'content' in data else ''
    if not chat_uuid or not content:
        response_code = 400
        error_message = 'Invalid parameter.'
        result_dict = create_error_info(message = error_message, status = response_code, path = 'POST /chat_history/prompt', details=error_message)
        return jsonify(result_dict), response_code

    try:
        response_code = 500 # デフォルトのレスポンスコード

        # チャット情報の取得
        chatInfo = None
        if chat_uuid:
            chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        else:
            # まだチャットが開始されていない場合、何もせず正常終了する。
            response_code = 200
            return jsonify(result_dict), response_code

        if chatInfo:
            # 既存のチャット履歴を返す
            record = ChatHistory.query.filter(
                ChatHistory.chat_no == chatInfo.chat_no
            ).order_by(ChatHistory.seq.asc()).first()

            # チャットメッセージを更新する
            if record:
                record.content = content
                record.is_updated = True
                db.session.add(record)

            # 変更をコミット
            db.session.commit()

        response_code = 200
        result_dict['result'] = True
    except Exception as e:
        app_logger.exception(f'POST /chat_history/prompt(chat_uuid={chat_uuid}) で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        result_dict = create_error_info(message = error_message, status = response_code, path = 'POST /chat_history/prompt', details=error_message)

    return jsonify(result_dict), response_code

def get_user_prompt_common(chat_uuid, role_no):
    chatInfo = get_or_create_chat_info(chat_uuid=chat_uuid, user=current_user)

    # 各prompt_idの最大revisionを取得するサブクエリを作成
    subquery = db.session.query(
        ChatPrompts.chat_no, ChatPrompts.role_no,
        func.max(ChatPrompts.revision).label("max_revision")
    ).filter(ChatPrompts.chat_no == chatInfo.chat_no, ChatPrompts.role_no == role_no
    ).group_by(ChatPrompts.chat_no, ChatPrompts.role_no).subquery()

    system_prompt = db.session.query(ChatPrompts).join(
        subquery, 
        db.and_(
            ChatPrompts.chat_no == subquery.c.chat_no,
            ChatPrompts.revision == subquery.c.max_revision
        )
    ).filter(
        ChatPrompts.role_no == 1
    ).order_by(ChatPrompts.updated_time.desc()).first()

    return system_prompt

@app.route('/chat_history/user_prompt', methods=['GET'])
@login_required
def get_user_prompt():
    app_logger = logging.getLogger('app_logger')
    chat_uuid = request.args.get('chat_uuid')
    role_no = 1  # user

    result_dict = {'result': False}
    response_code = 500
    try:
        if chat_uuid:
            user_prompt = get_user_prompt_common(chat_uuid, role_no)

            response_code = 200
            result_dict['result'] = True
            result_dict['prompt_content'] = ''
            result_dict['user_prompt_revision'] = 0
            if user_prompt:
                result_dict['prompt_content'] = user_prompt.prompt_content
                result_dict['user_prompt_revision'] = user_prompt.revision

            # 変更をコミット
            db.session.commit()

    except Exception as e:
        app_logger.exception(f'GET /chat_history/user_prompt(chat_uuid={chat_uuid}) で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        response_code = 500
        result_dict = create_error_info(message = error_message, status = response_code, path = 'GET /chat_history/user_prompt', details=error_message)

    return jsonify(result_dict), response_code

@app.route('/chat_history/user_prompt', methods=['POST'])
@login_required
def update_user_prompt():
    app_logger = logging.getLogger('app_logger')
    result_dict = {'result': False}
    response_code = 500

    # パラメータを受け取る
    data = request.get_json()
    chat_uuid = data['chat_uuid'] if 'chat_uuid' in data else ''
    revision = data['revision'] if 'revision' in data else '0'
    content = data['content'] if 'content' in data else ''
    role_no = 1  # user
    if not chat_uuid or not content or not revision.isdigit() or int(revision) < 0:
        response_code = 400
        error_message = 'Invalid parameter.'
        result_dict = create_error_info(message = error_message, status = response_code, path = 'POST /chat_history/user_prompt', details=error_message)
        return jsonify(result_dict), response_code

    try:
        revision = int(revision)
        response_code = 500 # デフォルトのレスポンスコード

        # チャット情報の取得
        chatInfo = None
        if chat_uuid:
            chatInfo = get_or_create_chat_info(chat_uuid=chat_uuid, user=current_user)
        else:
            # まだチャットが開始されていない場合、何もせず正常終了する。
            response_code = 200
            return jsonify(result_dict), response_code

        if chatInfo:
            user_prompt = get_user_prompt_common(chat_uuid, role_no)

            if (user_prompt and user_prompt.revision == revision) or (not user_prompt and revision == 0):
                updated_user_prompt = ChatPrompts(
                    chat_no=chatInfo.chat_no,
                    role_no=role_no,
                    revision=revision + 1,
                    prompt_content=content, 
                    user_no=current_user.user_no,
                    updated_time=get_current_time())

                db.session.add(updated_user_prompt)

                # 変更をコミット
                db.session.commit()

                response_code = 200
                result_dict['result'] = True

        else:
            error_message = f'User Promptの更新時にChat情報が取得できませんでした。(chat_uuid={chat_uuid})'
            app_logger.warn(error_message)
            result_dict = create_error_info(message = error_message, status = response_code, path = 'POST /chat_history/user_prompt', details=error_message)

    except Exception as e:
        app_logger.exception(f'POST /chat_history/user_prompt(chat_uuid={chat_uuid}) で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        result_dict = create_error_info(message = error_message, status = response_code, path = 'POST /chat_history/user_prompt', details=error_message)

    return jsonify(result_dict), response_code

def replace_for_voice(text) -> str:
    json_file = app.config['VOICE_REPLACE_RULE_FILE'] + '.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        replacement_dict = json.load(f)

    result = text
    for key, value in replacement_dict.items():
        result = result.replace(key, value)
    return result


def cleanup_wavs(folder_path, chat_uuid):
    file_pattern = 'c-' + chat_uuid + '*.wav'  # ファイル名のパターン

    # フォルダ内の条件に合致するファイルを取得
    file_list = glob.glob(os.path.join(folder_path, file_pattern))

    # ファイルを削除する
    for file_path in file_list:
        os.remove(file_path)

def trim_summary_message(raw_summary_message):
    """
    - raw_summary_message: /hist 直後のassistantのメッセージ。

    戻り値:
    引数から、前後の「```」を除去して返します。
    """

    # 改行を除いた部分を取得する
    start = raw_summary_message.find("```")
    end = raw_summary_message.rfind("```")
    if start < 0:
        start = 0
    else:
        start = start + 3
    if end < 0:
        end = len(raw_summary_message)
    extracted = raw_summary_message[start:end].strip()

    # 冒頭の ``` の後の改行を除く
    extracted = extracted.lstrip("\n")

    return extracted

def readSystemPrompot(promptName):
    app_logger = logging.getLogger('app_logger')
    data = ''
    try:
        with open(f'./prompts/{promptName}.md', 'r', encoding='UTF-8') as f:
            data = f.read()
    except:
        app_logger.exception('システムプロンプトファイルの読み込みに失敗しました。')
    return data

def makeSystemPrompot(prompt, summary_message=None):
    replaced = ''
    keyword = '{%%%history_summary%%%}'

    if keyword in prompt:
        if not summary_message:
            summary_message = 'None'
        replaced = prompt.replace(keyword, summary_message)
    elif summary_message:
        replaced = prompt + '  \n' + summary_message
    else:
        replaced = prompt
    return replaced

def list_md_files():
    # Flaskアプリのルートディレクトリを取得
    root_dir = app.root_path
    # 目的のディレクトリのパスを作成
    target_dir = os.path.join(root_dir, '..', 'prompts')
    # 目的のディレクトリ内の .md ファイルをリストアップ
    md_files = glob.glob(f"{target_dir}/*.md")
    return sorted([os.path.splitext(os.path.basename(file))[0] for file in md_files])

def is_system_prompt_file(file_title):
    return file_title in list_md_files()

def get_face_file_path_list(reverse=False):
    image_folder = os.path.join(app.root_path, 'static/faces')
    # reverseパラメータに基づいてソート順を変更
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))], reverse=reverse)
    image_urls = [url_for('static', filename=f'faces/{f}') for f in image_files]
    return image_urls

@app.route('/chat_history/word-replace', methods=['GET'])
@login_required
def get_word_replace():
    pass

@app.route('/chat_history/word-replace', methods=['POST'])
@login_required
def save_word_replace():
    app_logger = logging.getLogger('app_logger')
    chat_uuid = request.form.get('chat_uuid')
    is_assistants = []
    keys = request.form.getlist('keys[]')
    values = request.form.getlist('values[]')
    result_dict = {}
    response_code = 500

    app_logger.debug('@@@@@@@@@@ chat_uuid=' + str(chat_uuid))
    app_logger.debug('@@@@@@@@@@ keys=' + str(keys))
    app_logger.debug('@@@@@@@@@@ values=' + str(values))

    # is_assistantの値を取得する
    size = len(keys)
    index = 0
    while len(is_assistants) < size and index < 100:
        val = request.form.get('isAssistant_' + str(index))
        if val != None:
            is_assistants.append(val)
        index = index + 1

    app_logger.debug('@@@@@@@@@@ is_assistants=' + str(is_assistants))        
    if len(is_assistants) != size:
        # エラー
        error_message = 'is_assistantが正しく取得できませんでした。'
        response_code = 500
        result_dict = create_error_info(message = error_message, status = response_code, path = 'POST /chat_history/word-replace', details=error_message)
        return jsonify(result_dict), response_code

    try:
        chatInfo = get_or_create_chat_info(chat_uuid, current_user)
        app_logger.debug(f'@@@@@@@@@@ chat_no=[{chatInfo.chat_no}]')  
        word_replacings = WordReplacing.query.filter_by(chat_no=chatInfo.chat_no, is_deleted=False).order_by(WordReplacing.seq.asc()).all()
        for record in word_replacings:
            # このレコードの情報
            role = 'assistant' if record.is_assistant == 1 else 'user'
            word_client = record.word_client
            word_server = record.word_server
            app_logger.debug(f'@@@@@@@@@@ server: role=[{role}], word_client=[{word_client}], word_server=[{word_server}]')   

            # パラメータのレコードと一致するか
            is_match = False
            for i in range(0, size):
                p_role = is_assistants[i]
                p_word_client = keys[i]
                p_word_server = values[i]
                app_logger.debug(f'@@@@@@@@@@ parameter: p_role=[{p_role}], p_word_client=[{p_word_client}], p_word_server=[{p_word_server}]')   

                if role == p_role and word_client == p_word_client and word_server == p_word_server:
                    app_logger.debug(f'@@@@@@@@@@ MATCH!!!!!')   
                    is_match = True
                    is_assistants[i] = 'duplicated'
                    break

            if not is_match:
                # レコードを削除
                record.is_deleted = True
                record.delete_time = get_current_time()
                db.session.add(record)
                app_logger.debug(f'@@@@@@@@@@ server not match, delete!: role=[{role}], word_client=[{word_client}], word_server=[{word_server}]')   

        for i in range(0, size):
            p_role = is_assistants[i]
            p_word_client = keys[i]
            p_word_server = values[i]

            if p_role != 'duplicated':
                # パラメータを登録
                p_record = WordReplacing(
                    chat_no=chatInfo.chat_no,
                    is_assistant=1 if p_role == 'assistant' else 0,
                    word_client=p_word_client,
                    word_server=p_word_server, 
                    user_no=current_user.user_no,
                    updated_time=get_current_time(),
                    is_deleted=False)
                db.session.add(p_record)
                app_logger.debug(f'@@@@@@@@@@ parameter not match, insert!!: p_role=[{p_role}], p_word_client=[{p_word_client}], p_word_server=[{p_word_server}]')   

        db.session.commit()
        app_logger.debug(f'@@@@@@@@@@ Commit, OK!')   
        result_dict['result'] = True
        response_code = 200
    
    except Exception as e:
        app_logger.exception(f'POST /chat_history/word-replace で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        response_code = 500
        result_dict = create_error_info(message = error_message, status = response_code, path = '/chat_history/{seq}', details=error_message)

    return jsonify(result_dict), response_code

@app.route('/')
@login_required
def index():
    app_logger = logging.getLogger('app_logger')

    # VOICEVOXのspeaker番号を取得する
    voicevoxProtocol = app.config['VOICEVOX_PROTOCOL']
    voicevoxHost = app.config['VOICEVOX_HOST']
    voicevoxPort = app.config['VOICEVOX_PORT']
    speakers = voicevox.get_speakers(protocol=voicevoxProtocol, host=voicevoxHost, port=voicevoxPort)

    chat_uuid = request.args.get('chat_uuid')
    chatInfo = None
    if chat_uuid:
        chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
    chat_history_list = []
    word_replasing_list = []
    chat_name = ''
    image_url = ''
    # デフォルトモデルを設定
    model_id = get_default_model()['id']
    chat_no = 0
    if chatInfo:
        # 既存のチャット履歴を返す
        chat_history = ChatHistory.query.filter_by(chat_no=chatInfo.chat_no, is_deleted=False).order_by(ChatHistory.seq.asc()).all()

        # /hist の要素を除去する
        for i in range(len(chat_history) - 1, 0, -1):
            if chat_history[i].content == '/hist':
                del chat_history[i:i+2]

        image_url = chatInfo.assistant_pic_url
        if not image_url:
            image_url = url_for('static', filename=f'faces/{app.config["DEFAULT_ASSISTANT_PIC"]}')
        chat_history_list = [{'role': ch.role, 'content': ch.content, 'image_url': image_url if 'assistant' == ch.role else '', 'moderation': ch.moderation_color, 'seq': ch.seq, 'model_name': get_model_name_by_id(ch.model_id)} for ch in chat_history]
        if len(chat_history_list) > 0:
            chat_history_list.pop(0)  # 先頭のシステムプロンプトを削除
            # 最後のチャットのモデルを取得する
            current_model_id = chat_history[-1].model_id
            if current_model_id != None:
                model_id = current_model_id
        chat_name = chatInfo.chat_name
        chat_no = chatInfo.chat_no

        # ワード置換データを取得する
        word_replasings = WordReplacing.query.filter_by(chat_no=chatInfo.chat_no, is_deleted=False).order_by(WordReplacing.seq.asc()).all()
        word_replasing_list = [{'role': 'assistant' if record.is_assistant == 1 else 'user', 'word_client': record.word_client, 'word_server': record.word_server} for record in word_replasings]
    elif not chat_uuid:
        # ランダムなUUIDを生成
        chat_uuid = str(uuid.uuid4())

    chat_history_list = json.dumps(chat_history_list, default=str)

    # モデルの一覧を取得
    model_dict = {item['id']: item['model_name'] for item in ALL_MODEL_ID if item['enabled']}

    # 顔写真のURLのリストを取得する
    image_urls = get_face_file_path_list(reverse=True)
    image_urls = json.dumps(image_urls, default=str)

    word_replasing_list = json.dumps(word_replasing_list, default=str)

    system_prompts = get_prompt_list(current_user)
    system_prompts = [{'prompt_id': prompt.prompt_id, 'prompt_name': prompt.prompt_name, 'prompt_content': prompt.prompt_content} for prompt, x, y, z in system_prompts ]
    system_prompts = json.dumps(system_prompts, default=str)

    user_prompt = get_user_prompt_common(chat_uuid, 1)
    if user_prompt:
        # シリアル化可能な形に変換
        user_prompt = {
            'chat_no': user_prompt.chat_no,
            'role_no': user_prompt.role_no,
            'revision': user_prompt.revision,
            'prompt_content': user_prompt.prompt_content,
            'updated_time': user_prompt.updated_time
        }
    else:
        user_prompt = {}
    app_logger.debug(f'user_prompt: chat_uuid=[{chat_uuid}], user_prompt=[{str(user_prompt)}]')
    user_prompt = json.dumps(user_prompt, default=str)

    return render_template(
        'chatgpt.html', speakers=speakers, chat_no=chat_no, chat_uuid=chat_uuid, chat_name=chat_name, serialized_json=chat_history_list, model_id=model_id, model_dict=model_dict,
        assistant_pic_url_list=image_urls, word_replasing_list=word_replasing_list, system_prompt_list=system_prompts, user_prompt=user_prompt
    )

@app.route('/chat/list', methods=['GET'])
@login_required
def chat_list():
    app_logger = logging.getLogger('app_logger')

    try:
        # ChatHistoryの最新のレコードを取得するサブクエリ
        subquery = db.session.query(
            ChatHistory.chat_no,
            func.max(ChatHistory.seq).label("max_seq")
        ).filter(
            ChatHistory.is_deleted == False
        ).group_by(
            ChatHistory.chat_no
        ).subquery()

        chatInfos = db.session.query(
            ChatInfo.chat_uuid,
            ChatInfo.chat_name,
            ChatHistory.seq,
            ChatHistory.content,  # ChatHistoryの他のカラムを取得したい場合にはここを適宜変更
            ChatHistory.chat_time
        ).join(
            subquery,
            ChatInfo.chat_no == subquery.c.chat_no
        ).join(
            ChatHistory,
            (ChatHistory.chat_no == subquery.c.chat_no) & 
            (ChatHistory.seq == subquery.c.max_seq)
        ).filter(
            ChatInfo.user_no == current_user.user_no,
            ChatInfo.is_deleted == False,
            ChatHistory.is_deleted == False
        ).order_by(
            # ChatInfo.updated_time.desc()
            ChatHistory.chat_time.desc()
        ).all()

        chatInfos = [{'chat_uuid': item[0], 'chat_name': item[1], 'content': item[3], 'chat_time': item[4]} for item in chatInfos]
        chatInfos = json.dumps(chatInfos, default=str)

        return render_template(
            'chat_list.html', serialized_json=chatInfos
        ), 200
    except:
        app_logger.exception('チャット一覧の取得に失敗しました。')
        return render_template(
            'chat_list.html', chat_list=[]
        ), 500

@app.route('/chat/name', methods=['POST'])
@login_required
def chat_name_update():
    app_logger = logging.getLogger('app_logger')
    data = request.get_json()
    chat_uuid = data['chat_uuid']
    chat_name = data['chat_name']

    if is_empty(chat_name) or len(chat_name) > 30:
        status_code = 400
        error_info = create_error_info(message='チャット名を正しく入力してください。最大30文字までです。', status=status_code, path='/chat/name')
        return jsonify(error_info), status_code

    status_code = 500
    try:
        chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        if chatInfo:
            chatInfo.chat_name = chat_name
            chatInfo.updated_time = get_current_time()
            db.session.add(chatInfo)
            db.session.commit()
            status_code = 200
        else:
            app_logger.warn(f'チャットが見つかりません。chat_uuid={chat_uuid}, user_no={current_user.user_no}')
            status_code = 404

        return jsonify({}), status_code

    except:
        app_logger.exception('チャットの削除に失敗しました。')
        status_code = 500
        error_info = create_error_info(message='チャットの削除に失敗しました。', status=status_code, path='/chat/delete')

        return jsonify(error_info), status_code

@app.route('/chat/delete', methods=['POST'])
@login_required
def chat_delete():
    app_logger = logging.getLogger('app_logger')
    data = request.get_json()
    chat_uuid = data['chat_uuid']

    status_code = 500
    try:
        chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        if chatInfo:
            chatInfo.is_deleted = True
            chatInfo.delete_time = get_current_time()
            db.session.add(chatInfo)
            db.session.commit()
            status_code = 200
        else:
            app_logger.warn(f'チャットが見つかりません。chat_uuid={chat_uuid}, user_no={current_user.user_no}')
            status_code = 404

        return jsonify({}), status_code

    except:
        app_logger.exception(f'チャットの削除に失敗しました。chat_uuid={chat_uuid}')
        status_code = 500
        error_info = create_error_info(message='チャットの削除に失敗しました。', status=status_code, path='/chat/delete')

        return jsonify(error_info), status_code

@app.route('/chat/assistant-image', methods=['POST'])
@login_required
def chat_assistant_image_update():
    app_logger = logging.getLogger('app_logger')
    data = request.get_json()
    chat_uuid = data['chat_uuid']
    image_url = data['image_url']

    if is_empty(chat_uuid) or is_empty(image_url):
        status_code = 400
        error_info = create_error_info(message='Invalid request.', status=status_code, path='POST /chat/assistant-image')
        return jsonify(error_info), status_code

    status_code = 500
    result_dict = {}
    result_dict['result'] = False
    try:
        # chatInfo = ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=current_user.user_no).first()
        chatInfo = get_or_create_chat_info(chat_uuid=chat_uuid, user=current_user)
        if chatInfo:
            chatInfo.assistant_pic_url = image_url
            chatInfo.updated_time = get_current_time()
            db.session.add(chatInfo)
            db.session.commit()

        status_code = 200
        result_dict['result'] = True

        return jsonify(result_dict), status_code

    except:
        message = f'チャットの顔写真の更新に失敗しました。chat_uuid={chat_uuid}'
        app_logger.exception(message)
        status_code = 500
        error_info = create_error_info(message=message, status=status_code, path='POST /chat/assistant-image')

        return jsonify(error_info), status_code

@app.route('/chat/assistant-image', methods=['GET'])
@login_required
def chat_assistant_image_list():
    app_logger = logging.getLogger('app_logger')
    status_code = 200
 
    # 顔写真のURLのリストを取得する
    image_urls = get_face_file_path_list(reverse=True)
    result_dict = {
        'assistant_pic_url_list': image_urls 
    }
#    image_urls = json.dumps(image_urls, default=str)

    return jsonify(result_dict), status_code

import sqlite3
@app.route('/setup')
def setup():
    DATABASE = "instance/database.db"
    con = sqlite3.connect(DATABASE)

    # SQLファイルの内容を読み込む
    with open("./design/create_tables.sqlite3.sql", "r") as file:
        sql_script = file.read()
    with open("./design/first_data.sqlite3.sql", "r") as file:
        sql_script = sql_script + "\n" + file.read()

    # SQLスクリプトを実行する
    con.executescript(sql_script)
    
    con.close()
    return redirect(url_for('index'))

def is_positive_integer(s):
    return not s is None and s.isdigit() and len(s) <= 6
