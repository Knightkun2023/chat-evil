## CentOS7でサービスした記録

### サービスするFlaskアプリの構成の確認
今回サービスするFlaskアプリは次のような構成です。
```
/var/www/progs/chat-app
  ├─/flaskr
  │    ├─/static
  │    ├─/templates
  │    ├─/utils
  │    │    ├─__init__.py
  │    │    └─commons.py
  │    ├─__init__.py
  │    ├─chat.py
  │    ├─config.py
  │    ├─flaskapp.wsgi
  │    ├─log_config.py
  │    └─login.py
  ├─/logs
  │    └─app.log
  └─start.sh
```
実行パスは chat-app です。  
`app = Flask(__name__)` は`/flaskr/__init__.py`に記述しています。  
`/var/www/progs` 以下に次のコマンドを実行し、オーナーに作業者（ここでは`myaccount`）を、グループに`apache`を設定します。
```
chown -R myaccount:apache .
```

### Pythonのインストール
#### Pyenvのインストール
pyenvでPythonをインストールする。
```
git clone https://github.com/pyenv/pyenv.git /opt/.pyenv
```
環境変数を設定する。
```
echo 'export PYENV_ROOT="/opt/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
```
シェルの再起動。
```
source ~/.bashrc
```
Pythonのインストール
```
pyenv install 3.11.6
```
ここで、Python3.11.6のパスが後工程の設定で必要になる。
* python-home: /opt/.pyenv/versions/3.11.6
* python-path: /opt/.pyenv/versions/3.11.6/lib/python3.11/site-packages

#### OpenSSLの最新化
`pyenv install 3.11.6`が失敗した場合、そのエラーに応じてライブラリを最新化する。  
今回はOpenSSLのバージョンが足りなかったため、必要なバージョン以上にアップグレードした。
```
sudo yum install openssl-devel
```
yumで十分なバージョンがインストールできない場合は、ソースコードをビルドしてインストールする。  
コンパイル・ビルドに必要なライブラリをインストール・最新化する。
```
sudo yum install -y gcc make perl zlib-devel
```
適切なバージョンを取得し、ビルドする。
```
cd /tmp
wget https://www.openssl.org/source/openssl-1.1.1w.tar.gz

tar -xzf openssl-1.1.1w.tar.gz
cd openssl-1.1.1w
./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl shared zlib
make
sudo make install
```
インストールしたライブラリのパスを通した状態で再度`pyenv install 3.11.6`を実行した。
```
export PATH="/usr/local/ssl/bin:$PATH"
export LDFLAGS="-L/usr/local/ssl/lib"
export CPPFLAGS="-I/usr/local/ssl/include"
```
再度インストールしなおす。
```
pyenv install 3.11.6
```

### Apacheの最新化
```
sudo yum update httpd
sudo systemctl restart httpd
```

#### mod_wsgiの最新化
今回はPythonの仮想環境を使用しなかった。そのため、先にインストールした /opt/pyenv/versions/3.11.6 の下にそのままインストールする。  
`yum`でのインストールではバージョンが足りない可能性があるため、先にインストールしたPythonを元にインストールする。
```
pip install --upgrade pip
pip install mod_wsgi
```

次の場所にApacheのモジュールファイルが作成されています。
```
/opt/.pyenv/versions/3.11.6/lib/python3.11/site-packages/mod_wsgi/server/mod_wsgi-py311.cpython-311-x86_64-linux-gnu.so
```
このファイルをApacheのモジュールディレクトリにコピーします。
```
cp -p /opt/.pyenv/versions/3.11.6/lib/python3.11/site-packages/mod_wsgi/server/mod_wsgi-py311.cpython-311-x86_64-linux-gnu.so /usr/lib64/httpd/modules/.
```

### Apacheの設定

#### wsgiファイルの用意
##### /var/www/progs/chat-app/flaskr/flaskapp.wsgi
```
import sys
sys.path.insert(0, '/var/www/progs/chat-app')

import logging
# for log to apache logs.
logging.basicConfig(stream = sys.stderr)

import os

os.environ['FLASK_APP'] = 'flaskr'
os.environ['FLASK_ENV'] = 'development'
os.environ['OPENAI_API_KEY'] = '<API Key of OpenAI API>'
os.environ['GOOGLE_AI_API_KEY'] = '<API Key of Google AI API>'
os.environ['REMOTE_URL'] = '/chat-app'
os.environ['MODERATION_ACCESS_KEY'] = '12qw34er:testuser'
os.environ['SECRET_KEY'] = '9i8u7y6t5r4e3w2q'

from flaskr import app as application
```
このファイルには実行権限を着けます。
```
chmod a+x ./flaskr/flaskapp.wsgi
```

#### Apacheの設定ファイル

##### /etc/httpd/conf/httpd.conf
Pythonのパスを追加する。mod_wsgiの設定（`Include conf.modules.d/*.conf`）の前に追加する。
```
WSGIPythonHome /opt/.pyenv/versions/3.11.6
```

##### /etc/httpd/conf.d/ssl.conf
SSLの設定ファイルに下記を追記する。VirtualHostディレクティブの内部に記載する。
```
    # mod_wsgiの設定
    WSGIDaemonProcess flaskapp user=myaccount group=apache threads=5 python-home=/opt/.pyenv/versions/3.11.6 python-p
ath=/var/www/progs/chat-app:/opt/.pyenv/versions/3.11.6/lib/python3.11/site-packages home=/var/www/progs/chat-app
    WSGIScriptAlias /chat-app /var/www/progs/chat-app/flaskr/flaskapp.wsgi

    <Directory /var/www/progs/chat-app/flaskr>
        WSGIProcessGroup flaskapp
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
```
ここで、`myaccount`は作業者の通常ユーザーアカウントです。  
`WSGIDaemonProcess`に設定している内容は主に次の通りです。
* flaskapp : Flaskアプリ名
* user, group : 実行するユーザーのオーナーとグループ
* python-home : Pythonの実行ファイルのパス
* python-path : Pythonのライブラリパス
* home : Flaskの実行パス（working directory）

`WSGIScriptAlias`はApacheで動かす場合のコンテキストパスになります。

##### /etc/httpd/conf.modules.d/10-wsgi.conf
新しくインストールした`mod_wsgi.so`を指定します。
```
LoadModule wsgi_module "/usr/lib64/httpd/modules/mod_wsgi-py311.cpython-311-x86_64-linux-gnu.so"
```
既存の`wsgi_module`の記述があれば置き換えます。

#### Apacheの起動ファイル
Pythonのルートのsoファイルのディレクトリを追加します。

##### /etc/sysconfig/httpd
```
LD_LIBRARY_PATH=/opt/.pyenv/versions/3.11.6/lib:$LD_LIBRARY_PATH
```

### Apacheの再起動

```
sudo systemctl restart httpd
```
