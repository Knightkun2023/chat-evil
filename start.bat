@echo off
@rem このファイルをコピーして、start_xxx.sh 形式の起動ファイルとして保存してください。
@rem 各APIキーを発行したらそれぞれ設定してください。
@rem MODERATION_ACCESS_KEYは外部公開をする場合のみ設定が必要です。
@rem その他、リモートURL・ポートを任意に変更可能です。
@rem ただし、ポートはOS内で既に使用している場合は起動時にエラーになります。

@rem Activate venv
.\venv\Scripts\activate.bat

@rem Run Flask App
set FLASK_APP=flaskr
set FLASK_ENV=development
set DATABASE_URL=sqlite:///database.db
set OPENAI_API_KEY=<API Key of OpenAI API>
set GOOGLE_AI_API_KEY=<API Key of Google AI API>
set REMOTE_URL=http://127.0.0.1:5505
set MODERATION_ACCESS_KEY=Access Key 1:Recipient 1,Access Key 2:Recipient 2,...
for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(25))"') do set SECRET_KEY=%%i

flask run --port=5505
