@echo off
@rem ���̃t�@�C�����R�s�[���āAstart_xxx.sh �`���̋N���t�@�C���Ƃ��ĕۑ����Ă��������B
@rem �eAPI�L�[�𔭍s�����炻�ꂼ��ݒ肵�Ă��������B
@rem MODERATION_ACCESS_KEY�͊O�����J������ꍇ�̂ݐݒ肪�K�v�ł��B
@rem ���̑��A�����[�gURL�E�|�[�g��C�ӂɕύX�\�ł��B
@rem �������A�|�[�g��OS���Ŋ��Ɏg�p���Ă���ꍇ�͋N�����ɃG���[�ɂȂ�܂��B

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
