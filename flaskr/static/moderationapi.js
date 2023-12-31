(function() {
    function getContent() {
        var latestText = document.getElementById('prompt-textarea').textContent;
        if (latestText === '') {
            return '';
        }
/*
        // 直前のassistant
        var assistantElements = Array.from(document.querySelectorAll('.markdown.prose.w-full.break-words.dark\\:prose-invert.light')).slice(-1);
        if (assistantElements.length > 0) {
            assistantElements[0].querySelectorAll('p').forEach(target => {
                latestText = target.textContent + latestText;
            });

            // その前のuser
            var userElements = Array.from(document.querySelectorAll('.empty\\:hidden')).slice(-1).forEach(target => {
                latestText = target.textContent + latestText;
            });
        }*/

        return latestText;
    }

    // ローディングアイコンを表示する関数
    function showLoadingIcon() {
        document.getElementById('loadingIcon').style.display = 'block';
    }

    // ローディングアイコンを非表示にする関数
    function hideLoadingIcon() {
        document.getElementById('loadingIcon').style.display = 'none';
    }

    function changeBackgroundColorTextarea(color) {

        var textarea = document.getElementById("prompt-textarea").parentNode;
        var colorCd = '';

        // 一旦、全ての色関連クラスをリセット
        textarea.classList.remove('moderation-color-warn', 'moderation-color-critical', 'moderation-color-ok', 'moderation-color-error', 'quick-change');
    
        // 色を即座に変えるためのクラスを追加
        textarea.classList.add('quick-change');
    
        if (color === 'warn') {
            // colorCd = '#FFA580';  // オレンジ
            colorCd = 'moderation-color-warn';
        } else if (color === 'critical') {
            // colorCd = '#FFB6C1';  // 赤
            colorCd = 'moderation-color-critical';
        } else if (color === 'ok') {
            // colorCd = '#90EE90';  // 緑
            colorCd = 'moderation-color-ok';
        } else if (color === 'error') {
            // colorCd = '#D0D0D0';  // グレー
            colorCd = 'moderation-color-error';
        } else {
            return;
        }

        // 色を変える
        textarea.classList.add(colorCd);

        // 0.01秒後にquick-changeクラスを取り除く
        setTimeout(() => {
            textarea.classList.remove('quick-change');
        }, 10);
    
        // 4秒後に背景色を白に戻す
        setTimeout(function() {
            textarea.classList.remove('moderation-color-warn', 'moderation-color-critical', 'moderation-color-ok', 'moderation-color-error');
        }, 4000);
    }

    function getModerationResult() {
        // テキストエリアを白くする
        changeBackgroundColorTextarea('reset');

        var content = getContent();
        var csrf_token = "";  // $('#csrf_token').val();
        var moderation_model_no = "1";

        if (content === '') {
            return;
        }

        // リクエスト開始時にローディングアイコンを表示
        showLoadingIcon();

        fetch(MODERATION_REMOTE_URL + '/moderation/check2', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Chat-Url': window.location.href
            },
            body: JSON.stringify({
                'content': content,
                'moderation_model_no': moderation_model_no,
                'csrf_token': csrf_token
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(json => {
                    throw new Error(json.error_message || 'Unknown error');
                });
            }
            return response.json();
        })
        .then(data => {
            var done = false;
            if (data && data.result_val) {
                if (data.result_val === 'orange') {
                    changeBackgroundColorTextarea('warn');
                    done = true;
                } else if (data.result_val === 'red') {
                    changeBackgroundColorTextarea('critical');
                    done = true;
                } else if (data.result_val === 'ok') {
                    changeBackgroundColorTextarea('ok');
                    done = true;
                }
            }
            if (!done) {
                changeBackgroundColorTextarea('error');
            }
        })
        .catch(error => {
            console.error('Error:', error.message);
            changeBackgroundColorTextarea('error');
        })
        .finally(() => {
            // ローディングアイコンを非表示にする
            hideLoadingIcon();
        });

        return false;
    }

    /*
     * テキストエリアの背景色のスタイル設定を行う。
     */
    function initTextareaStyle() {
        var textareaStyleText = `
        /* 背景色をゆっくり変えるクラス */
        .slow-change {
            transition: background-color 2s; /* ゆっくり色を変える */
        }
        /* 背景色を急に変えるクラス */
        .quick-change {
            transition: background-color 0s; /* 即座に色を変える */
        }
        
        /* 背景色 */
        .moderation.moderation-color-ok {
            background-color: #90EE90C0;
            color: black;
        }
        .moderation.moderation-color-warn {
            background-color: #FFC966C0; /* #FFA580;*/
            color: black;
        }
        .moderation.moderation-color-critical {
            background-color: #FF0000C0;  /*#FFB6C1;*/
            color: white;
        }
        .moderation.moderation-color-error {
            background-color: #D0D0D0C0;
            color: black;
        }
        `;
        var textareaStyle = document.createElement('style');
        textareaStyle.innerHTML = textareaStyleText;
        document.head.appendChild(textareaStyle);
    }

    /*
     * テキストエリアの背景色のスタイル設定をテキストエリアに直接行う。
     */
    function initTextareaStyleOnTextarea() {
        // 事前にスタイルを設定
        var textarea = document.getElementById("prompt-textarea").parentNode;
        textarea.classList.add('slow-change');
        textarea.classList.add('moderation');
    }

    /*
     * ローディングアイコンの設定を行う。
     */
    function init_loadingIcon() {

        // ローディングアイコンのスタイルを追加
        var loadingStyleText = `
        #loadingIcon {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 9999;
            background-color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
        }
        
        #loadingIcon img {
            width: 50px;
            height: 50px;
        }
        `;
        var loadingStyle = document.createElement('style');
        loadingStyle.innerHTML = loadingStyleText;
        document.head.appendChild(loadingStyle);

        // ローディングアイコンを配置する
        var loadingDiv = document.createElement("div");
        loadingDiv.id = "loadingIcon";
        loadingDiv.style.display = "none";

        var img = document.createElement("img");
        img.src = MODERATION_REMOTE_URL + "/static/images/loading-loading-forever.gif";
        img.alt = "Loading...";

        loadingDiv.appendChild(img);
        document.body.appendChild(loadingDiv);
    }

    /*
     * モデレーションボタンのスタイル設定を行う。
     */
    function initModerationStyle() {

        // モデレーションボタンに付与するクラス
        var modBtnStyleText = `
        .moderation-text {
            display: none;
        }
        @media(min-width:420px){
            .moderation-text {
                display: inline;
            }
        }
        `;
        var modBtnStyle = document.createElement('style');
        modBtnStyle.innerHTML = modBtnStyleText;
        document.head.appendChild(modBtnStyle);
    }

    /*
     * モデレーションボタンの設定を行う。
     */
    function initModerationButton() {

        // モデレーションを行うボタンを配置する
        // 虫眼鏡のアイコン
        var spnIcon = document.createElement('span');
        spnIcon.innerHTML = '&#128269;';  // 虫眼鏡のアイコン

        // Moderationの文言
        var spnText = document.createElement('span');
        spnText.classList.add('moderation-text');
        spnText.innerHTML = '&nbsp;Moderation';
        
        // モデレーションボタン
        var btnModeration = document.createElement('button');
        btnModeration.id = 'btnModeration';
        btnModeration.type = 'button';
//        btnModeration.innerHTML = '&#128269;&nbsp;Moderation';
        btnModeration.classList.add('btn');
        btnModeration.classList.add('relative');
        if (window.innerWidth > 420) {
            btnModeration.classList.add('btn-neutral');
        }
        btnModeration.appendChild(spnIcon);
        btnModeration.appendChild(spnText);

        var targetElement = Array.from(document.querySelectorAll('div.grow:not(.absolute)')).slice(-1)[0];
        var nextElement = targetElement.nextElementSibling;
        if (nextElement) {
            targetElement.parentNode.insertBefore(btnModeration, nextElement);
        } else {
            targetElement.parentNode.appendChild(btnModeration);
        }

        btnModeration.addEventListener('click', getModerationResult);
    }

    // 初期化
    function init_moderation_proc() {

        // ローディングアイコンの設定
        init_loadingIcon();

        // テキストエリアを着色するためのスタイルを設定する
        initTextareaStyle();

        // テキストエリアに直接クラスを設定
        initTextareaStyleOnTextarea();

        // モデレーションボタンのスタイル設定
        initModerationStyle();

        // モデレーションボタンの設定
        initModerationButton();

        // New Chatや既存の他のChatを呼び出したときもモデレーションボタンを再表示させる設定
        setInterval(function() {
            // メイン領域にボタンが存在するかチェック
            if (!document.getElementById("btnModeration")) {
                // ボタンが存在しない場合、再度ボタンを追加するなどHTMLに書き込んだ処理を再度実行。
                initTextareaStyleOnTextarea();
                initModerationButton();
            }
        }, 2500);  // 2.5秒ごとにチェック
    }
    init_moderation_proc();

})();