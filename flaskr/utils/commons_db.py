from .. import db
from ..models.chat_db import ChatInfo
from ..models.system_prompts_db import SystemPrompts
from ..models.login_db import LoginUser
from .commons import get_current_time, CHAT_NAME_NEW
from sqlalchemy import func
from sqlalchemy.orm import aliased

def get_chat_info(chat_uuid:str, user):
    return ChatInfo.query.filter_by(chat_uuid=chat_uuid, user_no=user.user_no).first()

def get_or_create_chat_info(chat_uuid:str, user, chat_name = None):
    is_new_chat = False
    chatInfo = get_chat_info(chat_uuid, user)
    if chatInfo:
        if chat_name is not None and chat_name != chatInfo.chat_name:
            chatInfo.chat_name = chat_name
            chatInfo.updated_time = get_current_time()
            db.session.add(chatInfo)
    else:
        # chat_uuidを新たに登録する
        if chat_name is None:
            chat_name = CHAT_NAME_NEW
        chatInfo = ChatInfo(chat_uuid=chat_uuid, chat_name=chat_name, user_no=user.user_no, updated_time=get_current_time())
        is_new_chat = True
        db.session.add(chatInfo)
        db.session.flush()

    return chatInfo

def get_prompt_list(user):

    # 閲覧ユーザのユーザ番号
    current_user_no = user.user_no

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

    return system_prompts
