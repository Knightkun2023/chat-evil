# このファイルをコピーして、start_xxx.sh 形式の起動ファイルとして保存してください。
# 各APIキーを発行したらそれぞれ設定してください。
# MODERATION_ACCESS_KEYは外部公開をする場合のみ設定が必要です。
# その他、リモートURL・ポートを任意に変更可能です。
# ただし、ポートはOS内で既に使用している場合は起動時にエラーになります。

# Activate venv
.\venv\Scripts\Activate.ps1

# Run Flask App
$env:FLASK_APP="flaskr"
$env:FLASK_ENV="development"
$env:OPENAI_API_KEY="<API Key of OpenAI API>"
$env:GOOGLE_AI_API_KEY="<API Key of Google AI API>"
$env:REMOTE_URL="http://127.0.0.1:5505"
$env:MODERATION_ACCESS_KEY="Access Key 1:Recipient 1,Access Key 2:Recipient 2,..."
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(25))"

flask run --port=5505
