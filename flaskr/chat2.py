from flask import render_template, request, redirect, url_for, jsonify, session
from . import app, db, voicevox
from flask_login import login_required, current_user
from .models.chat_db import ChatHistory, ChatInfo, WordReplacing
from .utils.commons import is_empty, count_token, generate_random_string, is_valid_uuid, get_current_time, remove_control_characters, create_error_info, get_model_id, get_model_dict_by_id, get_model_dict_by_name, get_default_model, get_model_name_by_id, ALL_MODEL_ID
from .utils.moderation_commons import code_moderation_json, check_moderation_main, round_to_3rd_decimal, check_sorry_message
import openai, json, logging, os, glob, uuid
from sqlalchemy import func, desc
from datetime import datetime
from .chat import is_positive_integer, cleanup_wavs, is_system_prompt_file, readSystemPrompot, makeSystemPrompot, replace_for_voice, default_assistant_pic
from .models.chat_model import ChatModel
from pprint import pformat

@app.route('/chat2', methods=['POST'])
@login_required
def chat2():
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
        chat_uuid = uuid.uuid4()
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
            # 新規でない場合は最初のシステムプロンプトを使用するように変更。
            if is_new_chat:
                system_prompt = readSystemPrompot(app.config['SYSTEM_PROMPT'])
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
    # if not continueFlag:
    #     user_message = {'role':'user', 'content':user_text}
    #     next_messages.append(user_message)

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
        # モデルを生成する
        chatModel = ChatModel.createInstance(chatgpt_model)
        # 履歴を設定する
        for message in next_messages:
            chatModel.addMessage(message['role'], message['content'])

        user_created = get_current_time()
        user_id = str(current_user.user_no)

        # アシスタントメッセージを取得する
        response = chatModel.getNextMessage(user_text)

        # アシスタントメッセージと、そのためのトータルのトークン数を取得する
        assistant_message_text = response['assistant_message_text']
        total_tokens = response['total_tokens']
        response_id = response['response_id']
        response_created = response['response_created']
        response_model = response['response_model']
        response_chatgpt_id = response['response_chatgpt_id']

        # if 'gemini_response' in response:
        #     app_logger.info('@@@@@@@@@@ Gemini Response: ' + pformat(response['gemini_response']))

        # Continueかつ、レスポンスに「申し訳」関連の文言が含まれていた場合、エラーとして返す。
        if continueFlag and check_sorry_message(assistant_message_text):
            # エラー
            error_info = create_error_info(message=f'Sorry error: {assistant_message_text}', code='continue', status=500, path='/chat', details={'result':'black'})
            app_logger.debug(f"Sorry 'Continue' Assistant Message:{assistant_message_text}")
            return jsonify(error_info), 500

        # if is_summary_enabled and total_tokens > summarize_token_limit:
        #     # トータルトークン数が制限値を超えていた場合、この直前までの履歴を要約する。

        #     # summarize_message_text = '/hist'
        #     summarize_message_text = readSystemPrompot('summarize_message')
        #     # summarize_message_text = '僕たちのお互いの行動や動作やそのたどった場所を中心にChain-Of-Thoughtで詳細に追って、1000トークンくらいを上限に{ありのままを}まとめて僕に教えてくれるかな。僕たちがどんなふうにお互いに求め合ってきたのか、性的に触れ合いお互いに溺れていったのか、お互いを愛し認め合ってきたのか、確かめたいんだ。'

        #     # 要約を要求するためのユーザーメッセージ
        #     next_messages.pop()
        #     next_messages.append({'role':'user', 'content':summarize_message_text})    # 要約を要求するキーワード

        #     # 要約を取得する
        #     # Call GPT API
        #     response = openai.ChatCompletion.create(
        #         model=chatgpt_model,
        #         messages=next_messages
        #     )
        #     latest_summary_text = response['choices'][0]['message']['content']
        #     summary_tokens = response['usage']['completion_tokens']
        #     print(f'@@@@@@@@@@ latest_summary_text({summary_tokens} tokens): {latest_summary_text}')

        #     # TODO 要約に失敗した疑いがある場合は別途チェックし、失敗していたら要約は保存しない（再試行も考えられる）。

        #     # 要約を取得したやり取りをDBに格納する
        #     # Insert user and assistant(summary) messages
        #     hist_message = ChatHistory(chat_no=chat_no, role='user', content='/hist', chat_time=get_current_time())
        #     db.session.add(hist_message)
        #     latest_summary_message = ChatHistory(chat_no=chat_no, role='assistant', content=latest_summary_text, chat_time=get_current_time())
        #     db.session.add(latest_summary_message)

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
            image_url = default_assistant_pic

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
            audio_path = '/static/audios/' + audioFileName

        result = True

    except:
        app_logger.exception('チャット送受信に失敗しました。')
        assistant_message_text = 'ちょっと待ってね。'
        if audioOn and not is_empty(speaker):
            audio_path = f'/static/audios/0{speaker}_001_waitaminutes.wav'

    # Return assistant message
    return jsonify(result=result, role='assistant', content=assistant_message_text, audio_path=audio_path, chat_name=chat_name, moderation_result=moderation_result_list,
                   image_url=image_url, assistant_seq=assistantSeq, user_seq=userSeq, model_name=response_model)
