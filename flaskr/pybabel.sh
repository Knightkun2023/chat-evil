#!/bin/bash

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
elif [ "$1" = "compile" ]; then
    pybabel compile -d translations
else
    echo "Invalid argument"
fi

cd -