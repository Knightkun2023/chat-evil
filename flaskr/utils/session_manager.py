from enum import Enum
from datetime import datetime, timedelta
from flask import session
from .commons import TimeConstants, check_datetime_str
import logging

def remove_session_key(key: str) -> None:
    if key in session:
        del session[key]

def set_session(key: str, value: str, time_key: TimeConstants = None):
    app_logger = logging.getLogger('app_logger')

    if key is None or value is None:
        raise ValueError('key or value is None.')

    # 現在の日時を取得
    current_time = datetime.now()

    # 指定された秒数を加算
    expired_in_seconds = None
    if time_key is None:
        time_key = TimeConstants.ONE_YEAR

    expired_in_seconds = current_time + timedelta(seconds=time_key.value)

    # yyyyMMddHHmmss 形式に変換
    expire_time = expired_in_seconds.strftime("%Y%m%d%H%M%S")

    # sessionに追加
    value_with_expire_time = f'{expire_time}_{value}'
    app_logger.debug(f'@@@@@@@@@@ put to session: key=[{key}], value_with_expire_time=[{value_with_expire_time}]')
    session[key] = value_with_expire_time

def get_session(key: str, time_key: TimeConstants = None) -> str:
    app_logger = logging.getLogger('app_logger')
    
    if key is None:
        raise ValueError('key is None.')
    
    if key in session and session[key] is not None:
        value_with_expire_time = session[key]
        app_logger.debug(f'@@@@@@@@@@ get from session: key=[{key}], value_with_expire_time=[{value_with_expire_time}]')

        # セッション値のフォーマットチェック
        if len(value_with_expire_time) < 16 or value_with_expire_time[14] != '_' or not check_datetime_str(value_with_expire_time[:14]):
            # NG
            remove_session_key(key)
            return None

        expire_time = value_with_expire_time[:14]
        value = value_with_expire_time[15:]
        app_logger.debug(f'@@@@@@@@@@ get from session: expire_time=[{expire_time}], value=[{value}]')

        expire_datetime = datetime.strptime(expire_time, "%Y%m%d%H%M%S")
        if datetime.now() <= expire_datetime:
            # 期限内

            if time_key is not None:
                # セッション期限を延長する
                set_session(key, value, time_key)

            app_logger.debug(f'@@@@@@@@@@ get value=[{value}]')
            return value

    app_logger.debug(f'@@@@@@@@@@ dont get value')
    remove_session_key(key)
    return None

def set_session_for_csrf_token(key: str, value: str):
    set_session(key, value, TimeConstants.THREE_HOURS)

def get_session_for_csrf_token(key: str):
    return get_session(key, TimeConstants.THREE_HOURS)
