from flask import render_template, request, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import func
from . import app, db
from .models.chat_db import ChatHistory, ChatPrompts
from .models.chat_model import ChatModel
from .utils.commons import get_default_model, create_error_info, get_model_dict_by_id
from .utils.commons_db import get_chat_info
import logging

@app.route('/user-chat', methods=['POST'])
@login_required
def user_chat():
    app_logger = logging.getLogger('app_logger')
    result_dict = {}
    response_code = 500

    # パラメータを受け取る
    data = request.get_json()
    chat_uuid = data['chat_uuid'] if 'chat_uuid' in data else ''
    model_id = data['model_id'] if 'model_id' in data else str(get_default_model()['id'])
    app_logger.debug(f'@@@@@@@@@@ model_id=[{model_id}]')

    # 使用するモデルを取得する
    chatgpt_model = ''
    if model_id and model_id.isdigit():
        model_dict = get_model_dict_by_id(int(model_id))
        chatgpt_model = model_dict['model_name']
    if not chatgpt_model:
        chatgpt_model = app.config['CHATGPT_MODEL']
    app_logger.debug(f'@@@@@@@@@@ chatgpt_model=[{chatgpt_model}]')

    try:
        chatInfo = get_chat_info(chat_uuid=chat_uuid, user=current_user)
        if not chatInfo:
            raise ValueError(f'チャット情報がないとuser-chatは利用できません。')

        chat_history = ChatHistory.query.filter_by(chat_no=chatInfo.chat_no, is_deleted = False).order_by(ChatHistory.seq.asc()).all()
        chat_history_list = [{'role': ch.role, 'content': ch.content} if ch.name is not None else {'role': ch.role, 'content': ch.content} for ch in chat_history]
        if len(chat_history_list) == 0:
            raise ValueError(f'チャットを開始していないとuser-chatは利用できません。')
        if chat_history_list[-1]['role'] != 'assistant':
            raise ValueError(f'チャット履歴の最新がassistantではないためuser-promptを続行できません。')

        # 先頭がシステムプロンプトであった場合は削除する
        if chat_history_list[0]['role'] == 'system':
            chat_history_list.pop(0)

        # prompt_idの最大revisionを取得するサブクエリを作成
        subquery = db.session.query(
            ChatPrompts.chat_no,
            ChatPrompts.role_no,
            func.max(ChatPrompts.revision).label("max_revision")
        ).filter(ChatPrompts.chat_no == chatInfo.chat_no, ChatPrompts.role_no == 1, ChatPrompts.user_no == current_user.user_no
        ).group_by(ChatPrompts.chat_no, ChatPrompts.role_no).subquery()

        chat_prompt = db.session.query(ChatPrompts).join(
            subquery, 
            db.and_(
                ChatPrompts.chat_no == subquery.c.chat_no,
                ChatPrompts.role_no == subquery.c.role_no,
                ChatPrompts.revision == subquery.c.max_revision
            )
        ).filter(
            # ChatPrompts.is_deleted == False,
            ChatPrompts.user_no == current_user.user_no
        ).first()

        if not chat_prompt:
            raise ValueError(f'chatPromptレコードがないためuser-promptを続行できません。')

        chat_prompt_record = {'role': 'system', 'content': chat_prompt.prompt_content}
        chat_history_list.insert(0, chat_prompt_record)
        latest_assistant_message = chat_history_list.pop()

        # モデルを生成する
        chatModel = ChatModel.createInstance(chatgpt_model)
        # 履歴を設定する
        for message in chat_history_list:
            role = 'assistant' if message['role'] == 'user' else 'user'
            content = message['content']
            chatModel.addMessage(role, message['content'])
            app_logger.debug(f'@@@@@@@@@@ [history] role=[{role}], content=[{content}]')

        # ユーザーメッセージを取得する
        latest_content = latest_assistant_message['content']
        app_logger.debug(f'@@@@@@@@@@ [chatModel.getNextMessage] latest_content=[{latest_content}]')
        response = chatModel.getNextMessage(latest_content)

        # ユーザーメッセージと、そのためのトータルのトークン数を取得する
        assistant_message_text = response['assistant_message_text']
        app_logger.debug(f'assistant_message_text=[{assistant_message_text}]')

        result_dict['result'] = True
        result_dict['content'] = assistant_message_text
        response_code = 200

    except Exception as e:
        app_logger.exception(f'POST /user-chat で例外が発生しました。')
        # エラーの原因を取得
        error_message = str(e)
        response_code = 500
        result_dict = create_error_info(message = error_message, status = response_code, path = f'/user-chat/{chat_uuid}', details=error_message)

    return jsonify(result_dict), response_code
