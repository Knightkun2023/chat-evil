from flask import session
from datetime import datetime
from typing import Tuple
import string, random, tiktoken, uuid, re, logging
from urllib.parse import urlparse, parse_qs
from enum import Enum

class TimeConstants(Enum):
    ONE_YEAR = 60 * 60 * 24 * 365   # 1年の秒数
    THREE_HOURS = 60 * 60 * 3  # 3時間の秒数
    FIVE_MINUTES = 60 * 5   # 5分の秒数

def get_query_param_from_url(url, param_name):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get(param_name, [None])[0]

def is_empty(s) -> bool:
    if (type(s) == str):
        s = s.strip()
        if s == '':
            return True
        if is_numeric(s):
            if int(s) != 0:
                return False
            return True
        return False
    return not bool(s)

def valid_datetime(dt) -> bool:
    try:
        # strptimeは文字列を日時オブジェクトに変換します
        # 引数には変換したい文字列とその形式を指定します
        datetime.strptime(dt, '%Y%m%d%H%M%S%f')
        return True
    except ValueError:
        # ValueErrorが発生した場合は、引数の文字列が指定した形式に従っていないことを意味します
        return False

def is_valid_uuid(uuid_str):
    try:
        uuid_obj = uuid.UUID(uuid_str)
        return str(uuid_obj) == uuid_str  # 正しい形式のUUIDであればTrueを返す
    except ValueError:
        return False  # UUIDの形式でない場合はFalseを返す

def is_numeric(s) -> bool:
    return bool(s) and s.isdigit()

def get_current_time() -> str:
    return datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]

def get_display_time(s) -> str:
    # 入力の文字列を解析する
    dt = datetime.strptime(s, '%Y%m%d%H%M%S%f')

    # datetimeオブジェクトを任意の文字列形式に変換する
    # ここでは例として、'%Y-%m-%d %H:%M:%S'形式に変換するとします。
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def checkbox_to_save(c) -> int:
    if '1' == c:
        return True
    return False

def is_checked(b) -> str:
    if b:
        return ' checked'
    return ' '

def is_disabled(b) -> str:
    if b:
        return ' disabled'
    return ' '

def generate_random_string(length=48) -> str:
    # string.ascii_lettersには半角アルファベット（大文字小文字両方）が含まれています
    # string.digitsには0から9までの数字が含まれています
    characters = string.ascii_letters + string.digits

    # 指定した長さのランダムな文字列を生成
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    return random_string

import re

def is_alnum(s) -> bool:
    return re.match(r'^[a-zA-Z0-9-_]*$', s) is not None

def is_alpha_digits(s, min, max, required=False) -> bool:
    if required:
        if is_empty(s):
            return False
    if not is_empty(s):
        if len(s) < min or len(s) > max or not is_alnum(s):
            return False
    return True

def count_token(s):
    encoding = tiktoken.get_encoding('cl100k_base')
    return len(encoding.encode(s))   # トークン数を返す。

def remove_control_characters(input_string):
    # 制御文字を除去する正規表現パターン
    control_chars = ''.join(map(chr, list(range(0, 32)))) + ''.join(map(chr, list(range(127, 160))))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', input_string)

def create_error_info(message = '', details = {}, status = 500, path = '', code = '') -> dict:
    '''
    エラーレスポンスを生成して返す。
    
    :param message: エラーメッセージを示す文字列。デフォルトは空文字。
    :param details: エラー詳細情報
    :param status: エラーのステータスを示す整数。デフォルトは500。
    :param path: エラーが発生したリソースのパスを示す文字列。デフォルトは空文字。
    :param code: エラーコードを示す文字列。デフォルトは空文字。
    :return: エラー情報を含む辞書。
    '''
    return {
        'error': {
            'code': code,
            'message': message,
            'status': status,
            'path': path,
            'details': details,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }
    }

# ChatGPTのモデル名を保存用のIDに変換する。
CHATGPT_MODEL_ID = [
    {'id':0, 'model_name':'gpt-3.5-turbo', 'context_window':4000, 'enabled': False},
    {'id':1, 'model_name':'gpt-3.5-turbo-0301', 'context_window':4000, 'enabled': False},
    {'id':2, 'model_name':'gpt-3.5-turbo-0613', 'context_window':4000, 'enabled': False},
    {'id':8, 'model_name':'gpt-3.5-turbo-1106', 'context_window':16000, 'enabled': True},
    {'id':3, 'model_name':'gpt-3.5-turbo-16k', 'context_window':16000, 'enabled': False},
    {'id':4, 'model_name':'gpt-3.5-turbo-16k-0613', 'context_window':16000, 'enabled': False},
    # 'gpt-3.5-turbo-instruct',
    # 'gpt-3.5-turbo-instruct-0914',
    {'id':5, 'model_name':'gpt-4', 'context_window':8000, 'enabled': False},
    {'id':6, 'model_name':'gpt-4-0314', 'context_window':4000, 'enabled': False},
    {'id':7, 'model_name':'gpt-4-0613', 'context_window':8000, 'enabled': False},
    {'id':9, 'model_name':'gpt-4-1106-preview', 'context_window':128000, 'enabled': True},
    {'id':10, 'model_name':'gpt-4-vision-preview', 'context_window':128000, 'enabled': False}
]

GEMINI_MODEL_ID = [
    {'id': 1001, 'model_name': 'gemini-pro', 'context_window':30000, 'enabled': True},
    {'id': 1002, 'model_name': 'gemini-pro-vision', 'context_window':16000, 'enabled': False},
]

ALL_MODEL_ID = CHATGPT_MODEL_ID + GEMINI_MODEL_ID

ALL_MODEL_DICT = {ch['id']: ch for ch in ALL_MODEL_ID}

def get_model_name_by_id(id) -> str:
    if type(id) is int and id in ALL_MODEL_DICT:
        return ALL_MODEL_DICT[id]['model_name']
    return ''

def get_default_model() -> dict:
    for model_dict in ALL_MODEL_ID:
        if model_dict['enabled']:
            return model_dict
    return {}

def get_all_model_dict(key: str, value) -> dict:
    '''
    指定したkeyが指定したvalueである要素を返す。
    '''
    for index, model in enumerate(ALL_MODEL_ID):
        if model[key] == value:
            return model
    return None  # モデルが見つからない場合

def get_model_dict_by_id(model_id: int) -> dict:
    '''
    モデルIDに対応するChatGPTのモデル情報を返す。
    '''
    if type(model_id) != int or model_id < 0:
        return None
    return get_all_model_dict('id', model_id)

def get_model_dict_by_name(model_name: str) -> dict:
    '''
    モデル名に対応するChatGPTのモデル情報を返す。
    '''
    return get_all_model_dict('model_name', model_name)

def get_model_id(model_name: str) -> int:
    '''
    ChatGPTのモデル名に対応するIDを返す。
    '''
    model_dict = get_all_model_dict('model_name', model_name)
    if model_dict:
        return model_dict['id']
    return None  # モデルが見つからない場合

def check_model(model_name) -> bool:
    model_dict = get_all_model_dict('model_name', model_name)
    if model_dict:
        return True
    return False  # モデルが見つからない場合

def set_message_to_session(domain: str, id='_', main_message=None, error_message=None) -> None:
    '''
    セッションにメッセージを設定する。

    Parameters
    ----------
    domain : str
        メッセージを表示する対象のデータドメイン。
    id : Any, default '_'
        domainの個別のデータを表すid。一覧画面などドメイン全体を表す場合は「_」
    message : str, default ''
        エラーメッセージを示す文字列。デフォルトは空文字。
    error_message : str, default ''
        エラーメッセージを示す文字列。デフォルトは空文字。
    '''

    if not domain in session:
        session[domain] = {}

    dict = {}
    if main_message:
        dict['main_message'] = main_message
    elif error_message:
        dict['error_message'] = error_message
    if dict:
        id = str(id)
        session[domain][id] = dict

def get_message_from_session(domain: str, id='_') -> Tuple[str, str]:
    '''
    セッションからメッセージを取得する。取得したメッセージオブジェクトは削除される。

    Parameters
    ----------
    domain : str
        メッセージを表示する対象のデータドメイン。
    id : Any, default '_'

    Returns
    -------
    message : str, default None
        成功・情報メッセージを示す文字列。ない場合はNone。
    error_message : str, default None
        エラーメッセージを示す文字列。ない場合はNone。
    '''

    if not domain in session or not id in session[domain]:
        return None, None

    message = None if not 'main_message' in session[domain][id] else session[domain][id]['main_message']
    error_message = None if not 'error_message' in session[domain][id] else session[domain][id]['error_message']
    del session[domain][id]
    return message, error_message

def check_datetime_str(s: str) -> bool:
    app_logger = logging.getLogger('app_logger')
    app_logger.debug(f'@@@@@@@@@@ s=[{s}]')
    try:
        expire_datetime = None
        if len(s) == 14:
            app_logger.debug(f'@@@@@@@@@@ len(s)=14')
            expire_datetime = datetime.strptime(s, "%Y%m%d%H%M%S")
            app_logger.debug(f'@@@@@@@@@@ expire_datetime(14)=[{str(expire_datetime)}]')
        elif len(s) == 17:
            app_logger.debug(f'@@@@@@@@@@ len(s)=17')
            expire_datetime = datetime.strptime(s, "%Y%m%d%H%M%S%f")
            app_logger.debug(f'@@@@@@@@@@ expire_datetime(17)=[{str(expire_datetime)}]')
        
        if expire_datetime is not None:
            return True
    except:
        app_logger.debug(f'@@@@@@@@@@ except!')
        return False
