## How to setup & run 'Chat Evil'

### Pythonのインストール

#### Python for Mac
```
use brew -> pyenv  
```
https://prog-8.com/docs/python-env

#### Windowsの場合
Pythonをインストールしてください。  
また、今のところ次のツールのインストールが必要ですので、インストールを行ってください。
* Microsoft C++ Build Tools https://visualstudio.microsoft.com/ja/visual-cpp-build-tools/
「C++ によるデスクトップ開発」にのみチェックを入れてインストールします。
* Rust Compiler https://rustup.rs/
デフォルトのままインストールします。

インストールが完了したら、VSCodeなど実行環境を再起動してください。コマンドプロンプトならばコマンドプロンプトを開きなおしてください。

### プログラムの設定
Pythonをインストールしたら、リポジトリをcloneします。

```
git clone https://github.com/Knightkun2023/chat-evil.git
```
作成されたフォルダに移動し、次のコマンドを実行してvenv（仮想実行環境）を作成し、必要なライブラリをvenv内にインストールします。
```
python -m venv venv
```
次に、venvを有効化します。以降はvenv環境で設定・操作を行います。

#### Macの場合
```
source ./venv/bin/activate
```
#### Windowsバッチの場合
```
.\venv\Scripts\activate.bat
```
#### Windows PowerShellの場合
```
.\venv\Scripts\Activate.ps1
```
venvに入ったら、次のコマンドを実行して必要なライブラリをインストールします。
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
*\*including install openai library.*

#### How to upgrade requirements.txt
```
pip freeze > requirements.txt  
```

### Voice Environment (Optional)
Install and Run VOICEVOX  
https://voicevox.hiroshiba.jp/  

### config.py settings
Edit flaskr/config.py

### How to run Flask
起動スクリプト（start_xxx.yyy）ファイルを環境ごとに編集し、それを実行すると起動します。

#### Mac (Bash/zsh)
start.sh をコピーしてファイル名を start_xxx.sh に変更してください。そのファイルご自分の環境用に修正して起動ファイルとします。

#### Windows
start.bat をコピーしてファイル名を start_xxx.bat に変更してください。そのファイルご自分の環境用に修正して起動ファイルとします。

#### PowerShell (Windows)
start.ps1 をコピーしてファイル名を start_xxx.ps1 に変更してください。そのファイルご自分の環境用に修正して起動ファイルとします。  
※なお、ps1ファイルを用いたPowerShellでの動作の確認はしておりません。

## 利用登録コードの初回発行

```
INSERT INTO registration_codes (
    registration_code,
    remarks,
    is_used,
    issuing_user_no,
    issuing_time,
    expiration_time,
    is_deleted,
    roles
)
VALUES (
    'registration_code',
    '初回登録用',
    0,
    0,
    strftime('%Y%m%d%H%M%S', 'now', '+9 hours') || '000',
    strftime('%Y%m%d%H%M%S', 'now', '+10 hours') || '000',
    0,
    0
);
```

## Reference Links
【PythonでWebアプリ作成】Flask入門 ！この動画１本でWebアプリが作れちゃう！ 〜 Pythonプログラミング初心者用 〜  
https://www.youtube.com/watch?v=EQIAzH0HvzQ  

【話題の技術】ChatGPTのAPIをPythonから使う方法を解説！APIを使って議事録の要約プログラムを作ってみた！〜人工知能の進化が凄すぎる〜  
https://www.youtube.com/watch?v=kodz6fzbAUA  

【コピペでOK】CSSだけでLINE風の「吹き出し」を作る方法！  
https://stand-4u.com/css/fukidashi.html  

Free Icons | Font Awesome  
https://fontawesome.com/search?o=r&m=free&s=regular&f=classic  

WindowsでPIP Install するとSSLエラーになるのを解消する。  
https://qiita.com/kekosh/items/e96e822bf9cb6ca1aff8  

自然な会話できてすごい / JavaScriptで簡単に作れる  
https://www.youtube.com/watch?v=oOUBvdLKLK4  

ChatGPTとWhisperのAPIを使用して、AIと話せる会話アプリを作ってみた【Python初心者でも使えるコード付きで解説】  
https://www.youtube.com/watch?v=ECwfieE5hDU  
