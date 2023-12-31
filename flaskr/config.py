# 使用するChatGPTのモデル
CHATGPT_MODEL='gpt-3.5-turbo'
# CHATGPT_MODEL='gpt-4'

# 要約を行うかどうか
USE_SUMMARRIZATION=True

# サービス時のアプリケーションルート。必要に応じて '/flask' などを指定。
APPLICATION_ROOT=''

# 使用するシステムプロンプトファイル（拡張子 .md を除く）
SYSTEM_PROMPT = 'yukari'
# APIを実行する際にサーバーに渡す会話の履歴の数。冒頭のシステムプロンプトは常に付加するため、それ以外の直近の会話の数を指定する。
# 最新の会話は直近のユーザーの入力がそれにあたる。
ACTIVE_CHAT_HISTORY_LENGTH = 9
# システムプロンプト最大長
SYSTEM_PROMPT_MAX_LENGTH = 4000
# 要約を求めるトークン数。この数を越えると要約を求める。
SUMMARIZE_TOKEN_LIMIT = 3000
# SUMMARIZE_TOKEN_LIMIT = 5600 #7000
# 送信トークン上限。この数を超えるチャット（user / assistant）以前は送信messagesに含めない。
SEND_TOKEN_LIMIT = 3200
# SEND_TOKEN_LIMIT = 5600 #7450

## 要約をする際、直近のChatから遡り、次のどちらかまでは要約に含めずに残す。
# 要約時、要約対象としない直近のChatの会話数。user/assistantの一方向送信を1で数える。
REST_CHAT_SIZE=20
# 要約時、要約対象としない直近のChatのトークン数。
REST_TOKENS=2500

# ChatGPTの返答の最大トークン数
ASSISTANT_MAX_TOKENS = 150
# フリー提供用のキー
FREE_KEY='d7a2cd26-8f8a-ddcb-d306-461174283851'

# Protocol + Remote Host
REMOTE_URL='http://127.0.0.1:5505'

# VOICEVOX information
VOICEVOX_PROTOCOL = 'http'
VOICEVOX_HOST = 'localhost'
VOICEVOX_PORT = 50021

# 音声変換をする際の文字列変換ルールファイル（JSON。拡張子は小文字とし、ここでは記述不要）
VOICE_REPLACE_RULE_FILE='./materials/replace_for_voice'

# database settings
SQLALCHEMY_DATABASE_URI='sqlite:///database.db'

# Flask-Sessionによるセッションの格納先。filesystemはローカルファイル。他にredis、memcacheなどをサポートしている。
SESSION_TYPE='filesystem'

### ログイン関連
# 登録コードのデフォルトの有効期限（分）
EXPIRATION_MINUTES=1440*3  # 3日間