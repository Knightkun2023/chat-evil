#!/bin/bash

# PyBabelを用いた多言語翻訳を行うためのシェル。
# 手順は次お通り。
#  1. babel.cfgファイルを作成。既に用意済み。
#  2. テンプレートなどに必要な記述（ここでは「翻訳マーカー」と呼称）を行う。html, js, py などに記述できます。既存の記述を参考にしてください。
#  3. テンプレートなどの翻訳マーカーを抽出して設定ファイル（.potファイル）を作成する。flaskr/translations/messages.pot が作成される。
#  4. 翻訳マーカーが抽出された.potファイルから、翻訳を記述する.poファイルを作成する。flaskr/translations/ja/LC_MESSAGES/messages.pot が作成される。
#  5. .poファイルに翻訳を記載していく。
#  6. .poファイルをコンパイルし、.mo ファイルを作成する。flaskr/translations/ja/LC_MESSAGES/messages.mo が作成される。
#
# 本シェルでは 3, 4, 6 を行うためのものです。それぞれ、3: ext, 4: update, 6: compile を引数につけてください。
# なお、4.を初回に行う場合は pybabel init が行われます。

# シェルスクリプトのディレクトリパスを取得
script_dir="$(cd "$(dirname "$0")" && pwd)"

# shのあるディレクトリに移動
cd "$script_dir/"

if [ "$1" = "ext" ]; then
pybabel extract -F babel.cfg -k lazy_gettext -o translations/messages.pot .
    #pybabel init -i translations/messages.pot -d translations -l de
    #pybabel init -i translations/messages.pot -d translations -l es
    #pybabel init -i translations/messages.pot -d translations -l fr
    pybabel update -i translations/messages.pot -d translations -l ja
    #pybabel init -i translations/messages.pot -d translations -l ko
    #pybabel init -i translations/messages.pot -d translations -l pt
    #pybabel init -i translations/messages.pot -d translations -l uk
    #pybabel init -i translations/messages.pot -d translations -l zh_CN
    #pybabel init -i translations/messages.pot -d translations -l zh_TW
elif [ "$1" = "update" ]; then
    # .poファイルが存在するかどうかを確認
    if [ -f translations/ja/LC_MESSAGES/messages.po ]; then
        # .poファイルが存在する場合、updateを実行
        echo "Updating existing .po file..."
        pybabel update -i translations/messages.pot -d translations -l ja
    else
        # .poファイルが存在しない場合、initを実行
        echo "Initializing new .po file..."
        pybabel init -i translations/messages.pot -d translations -l ja
    fi
elif [ "$1" = "compile" ]; then
    pybabel compile -d translations
else
    echo "Invalid argument"
fi

cd -