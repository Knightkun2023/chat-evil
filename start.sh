#!/bin/bash

# このファイルをコピーして、start_xxx.sh 形式の起動ファイルとして保存してください。
# 各APIキーを発行したらそれぞれ設定してください。
# MODERATION_ACCESS_KEYは外部公開をする場合のみ設定が必要です。
# その他、リモートURL・ポートを任意に変更可能です。
# ただし、ポートはOS内で既に使用している場合は起動時にエラーになります。

# Activate venv
source venv/bin/activate

# Run Flask App
export FLASK_APP=flaskr
export FLASK_ENV=development
export OPENAI_API_KEY="<API Key of OpenAI API>"
export GOOGLE_AI_API_KEY="<API Key of OpenAI API>"
export REMOTE_URL=http://127.0.0.1:5505
export MODERATION_ACCESS_KEY='Access Key 1:Recipient 1,Access Key 2:Recipient 2,...'
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(25))')

flask run --port=5505
