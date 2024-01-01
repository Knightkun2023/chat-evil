# 使用するChatGPTのモデル
CHATGPT_MODEL='gpt-3.5-turbo'
# CHATGPT_MODEL='gpt-4'

# サービス時のアプリケーションルート。必要に応じて '/flask' などを指定。
APPLICATION_ROOT=''

# 使用するシステムプロンプトファイル（拡張子 .md を除く）
SYSTEM_PROMPT = 'yukari'
# システムプロンプト最大長
SYSTEM_PROMPT_MAX_LENGTH = 4000

# ChatGPTの返答の最大トークン数
ASSISTANT_MAX_TOKENS = 150

# Protocol + Remote Host
#REMOTE_URL='http://127.0.0.1:5505'

# VOICEVOX information
VOICEVOX_PROTOCOL = 'http'
VOICEVOX_HOST = 'localhost'
VOICEVOX_PORT = 50021

# 音声変換をする際の文字列変換ルールファイル（JSON。拡張子は小文字とし、ここでは記述不要）
VOICE_REPLACE_RULE_FILE='./materials/replace_for_voice'

# database settings
SQLALCHEMY_DATABASE_URI='sqlite:///database.db'
#SQLALCHEMY_DATABASE_URI="mysql+pymysql://username:password@localhost/dbname"

# Flask-Sessionによるセッションの格納先。filesystemはローカルファイル。他にredis、memcacheなどをサポートしている。
SESSION_TYPE='filesystem'

### ログイン関連
# 登録コードのデフォルトの有効期限（分）
EXPIRATION_MINUTES=1440*3  # 3日間

# デフォルトの顔
DEFAULT_ASSISTANT_PIC='/static/faces/20231231181229555.png'
