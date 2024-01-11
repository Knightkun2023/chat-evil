function setSaysIcons($saysDiv = undefined, isUser = false) {
    $saysDiv.append($('<i>').addClass('fa-solid').addClass('fa-pen').addClass('message-edit-icon'));     // 編集ボタン
    $saysDiv.append($('<i>').addClass('fa-regular').addClass('fa-clipboard').addClass('message-copy-icon'));     // コピーボタン
    $saysDiv.append($('<i>').addClass('fa-solid').addClass('fa-heart').addClass('warn-icon'));     // モデレーション警告アイコン
    if (isUser) {
        $saysDiv.append($('<i>').addClass('fa-solid').addClass('fa-rotate-left').addClass('message-resay-icon'));     // 再メッセージアイコン
    }

}

function replaceWordsClientToServer(text, role) {
    // userのもののみ。
    if (role !== 'user') {
        return text;
    }
    for (var i = 0; i < word_replasing_list.length; i++) {
        var item = word_replasing_list[i];
        if (item.role === role) {
            text = text.replace(new RegExp(item.word_client, 'g'), item.word_server);
        }
    }
    return text;
}

function replaceWordsServerToClient(text, role) {
    for (var i = 0; i < word_replasing_list.length; i++) {
        var item = word_replasing_list[i];
        if (item.role === role) {
            text = text.replace(new RegExp(item.word_server, 'g'), item.word_client);
        }
    }
    return text;
}

function appendContent(inputText, role, autoScroll = true, image_url = '', moderation='', seq=0, model_name='') {
    var $contentsField = $('#contents_field');

    // 特定のワードを置換する
    inputText = replaceWordsServerToClient(inputText, role);

    var $tmpInDiv = $('<span>').text(inputText);
    var $saysDiv = $('<div>').html($tmpInDiv.text().replace(/\n/g, '<br>')).addClass('says');
    var $messageBlock = $('<div>').addClass('message-block').addClass(role);
    if (seq !== 0) {
        $messageBlock.attr('message-seq', seq);
    }
    if (moderation == 'O') {
        $messageBlock.addClass('warning');
    } else if (moderation == 'R') {
        $messageBlock.addClass('critical');
    }
    if ('assistant' === role && image_url !== '') {
        // 顔アイコンを入れる
        let $assistant_img = $('<img>').addClass('assistant-img').attr("src", image_url);
        let $special_icon = $('<i>').addClass('fa-solid').addClass('fa-bolt-lightning').addClass('img-special-icon');     // スペシャルアイコン
        let $google_icon = $('<i>').addClass('fa-brands').addClass('fa-google').addClass('img-google-icon');     // Googleアイコン
        let $imgDiv = $('<div>').addClass('img-area');
        $imgDiv.append($assistant_img);
        $imgDiv.append($special_icon);
        $imgDiv.append($google_icon);
        $messageBlock.append($imgDiv);

        if (model_name !== undefined && typeof model_name === 'string' && model_name !== '') {
            if (!model_name.includes('gpt-3')) {
                if (model_name.includes('gemini')) {
                    $messageBlock.addClass('gemini-model');
                } else {
                    $messageBlock.addClass('special-model');
                }
            }
        }
    }

    // メッセージエリアのアイコンを設定する。
    setSaysIcons($saysDiv, 'user' === role);

    var $messageBlock = $messageBlock.append($saysDiv);
    $contentsField.append($messageBlock);

    if (autoScroll) {
        // スクロールする
        var h = $contentsField.prop('scrollHeight');
        $contentsField.delay(100).animate({
            scrollTop: h
        }, 1500);
    }
}

function initCustomizeSystemPrompt() {
    // 初期状態を設定
    if ($('#customize-system-prompt-on').prop('checked')) {
        $('#customize-system-prompt-toggle').click();
    }
    $('#customized_prompt').val('');
    $('#work_system_prompt').val('');
}

function getSystemPrompt(chat_uuid, f) {
    // Ajaxでシステムプロンプトを取得する。
    $.ajax({
        url: REMOTE_URL + '/chat_history/prompt',
        type: 'GET',
        contentType: 'application/json',
        data: { chat_uuid: chat_uuid },
        dataType: 'json',
        success: function(data) {
            // Assume that 'data' is an object and we want to extract 'content' from it
            var result = data.result;
            var system_prompt = data.system_prompt;
            if (result !== true) {
                console.log("result is not true. data=" + JSON.stringify(data, null, 2));  // This will print the data as a nicely formatted JSON string
            }

            $('#customized_prompt').val(system_prompt);
            f(system_prompt);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //#contents_field
            let undoLastChat = true;    // 送信したメッセージをテキストエリアに戻すか
            if (textStatus === 'timeout') {
                console.error('Request timed out');
                // タイムアウト処理
                showWarningMessage('リクエストがタイムアウトしました。', 5000);
            } else if (textStatus === 'parsererror') {
                console.error('Failed to parse JSON');
                // JSON解析エラーの処理
                showWarningMessage('レスポンスが不正です。', 5000);
            } else if (textStatus === 'error') {
                // その他のエラー処理
                const response = JSON.parse(jqXHR.responseText);
                console.error('Server responded with:', response);
                showWarningMessage('エラーが発生しました。', 5000);
            } else {
                console.error('Error', textStatus, errorThrown);
                // その他のエラー処理
                showWarningMessage('エラーが発生しました。', 5000);
            }
        }
    });
}

$(document).ready(function() {
    // textareaタグを全て取得
    $("#content_input").each(function() {
        // // デフォルト値としてスタイル属性を付与
        // $(this).css("height", $(this).prop("scrollHeight"));
  
        // inputイベントが発生するたびに関数呼び出し
        $(this).on("input", function() {
            // textareaの高さを計算して指定
            $(this).css("height", "auto");
            $(this).css("height", $(this).prop("scrollHeight") + "px");
            var divHeight = parseInt($(this).prop("scrollHeight")) + 2;
            $('.bottom-fixed').css("height", divHeight + "px");
            $('.scrollable-content').css("bottom", divHeight + "px");
        });
    });

    $(".toggle").on("click", function() {
        $(this).toggleClass("checked");
        var checkbox = $(this).find("input[type='checkbox']");
        checkbox.prop("checked", !checkbox.prop("checked"));

        if($(this).find("#audioOn").length) {
            if (checkbox.prop('checked')) {
                $('#audioCredit').show();
            } else {
                $('#audioCredit').hide();
    
                const audio = document.querySelector("audio");
                audio.pause();
            }
        }

        // システムプロンプトカスタマイズ
        if($(this).find("#customize-system-prompt-on").length) {
            if (checkbox.prop('checked')) {
                // カスタムプロンプト有効化
                $('#customize-system-prompt').prop('disabled', false);
                if ($('#customized_prompt').val() === '') {
                    var chat_uuid = $('#chat_uuid').val();
                    getSystemPrompt(chat_uuid, function(s) { $('#customized_prompt').val(s); });
                }
            } else {
                // カスタムプロンプト無効化
                $('#customize-system-prompt').prop('disabled', true);
                $('#customized_prompt').val('');
            }
        }
    });
    if ($('#audioToggle').prop('checked')) {
        $('#audioCredit').show();
    } else {
        $('#audioCredit').hide();
    }

    function saveSystemPromptHandler(e) {
        var chat_uuid = $('#chat_uuid').val();
        var updatedContent = $('#work_system_prompt').val();
        $.ajax({
            url: REMOTE_URL + '/chat_history/prompt',
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'X-Chat-Url': window.location.href
            },
            data: JSON.stringify({
                'chat_uuid': chat_uuid,
                'content': updatedContent
            }),
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error.message, 20000);
                }
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    }

    // $('#undo_by_default').click(function() {
    //     getSystemPrompt(mkuuid(), function(s) { $('#work_system_prompt').val(s); });
    // });
    function undoByDefault(e) {
        getSystemPrompt(mkuuid(), function(s) { $('#work_system_prompt').val(s); });
    }

    // $('#undo_by_saved').click(function() {
    //     var chat_uuid = $('#chat_uuid').val();
    //     getSystemPrompt(chat_uuid, function(s) { $('#work_system_prompt').val(s); });
    // });
    function undoBySaved() {
        var chat_uuid = $('#chat_uuid').val();
        getSystemPrompt(chat_uuid, function(s) { $('#work_system_prompt').val(s); });
    }

    const recognition = new webkitSpeechRecognition();
    recognition.lang = "ja";
    recognition.continuous = true;
    recognition.onresult = (event) => {
        const results = event.results;
        console.log(results[0][0].transcript);
        $('#content_input').val(results[0][0].transcript).trigger('input');
        submitToServer();
    };
    $('#btn_voiceRec').mousedown(function() {
        recognition.start();
    });
    $('#btn_voiceRec').mouseup(function() {
        recognition.stop();
    });

    // チャット履歴を表示させる。
    if (chat_history_list && chat_history_list.length > 0) {
        var item = null;
        for (var i = 0; i < chat_history_list.length - 1; i++) {
            item = chat_history_list[i];
            appendContent(item.content, item.role, false, item.image_url, item.moderation, item.seq, item.model_name);
        }
        // 一番最後に末尾までスクロールさせる。
        var item = chat_history_list[chat_history_list.length - 1];
        appendContent(item.content, item.role, true, item.image_url, item.moderation, item.seq, item.model_name);
    }

    if (system_prompt_list && system_prompt_list.length > 0) {
        var $select = $('#prompt_candidates');
        window.promptContents = {};
        $select.append($('<option>').val("0").text(gettext('(default)')));
        window.promptContents["0"] = "";
        for (var i = 0; i < system_prompt_list.length; i++) {
            var prompt_id = system_prompt_list[i].prompt_id;
            var prompt_name = system_prompt_list[i].prompt_name;
            var prompt_content = system_prompt_list[i].prompt_content;
            $select.append($('<option>').val(prompt_id).text(prompt_name));
            window.promptContents[prompt_id] = prompt_content;
        }
    }
    $('#prompt_candidates').change(function() {
        var prompt_id = $(this).val();
        if (prompt_id === "0") {
            $('#work_system_prompt').val($('#customized_prompt').val());
        }
        var prompt_content = window.promptContents[prompt_id];
        if (prompt_content !== "") {
            $('#work_system_prompt').val(prompt_content);
        }
    });

    $('#setting_button').click(function(event) {
        event.stopPropagation();  // これを追加
        $("#setting_modal").fadeIn(400);

        $(document).click(function(e) {
            let $target = $(e.target);
            if(!$target.closest('#setting_panel').length && $('#setting_panel').is(":visible")) {
                $("#setting_modal").fadeOut(400);
            }
        });
        $(document).on('click', '.btn-close-setting-panel', function() {
            // 親要素を探す
            const $modal = $(this).closest('#setting_modal');
    
            if(!$modal.closest('#setting_panel').length && $('#setting_panel').is(":visible")) {
                $("#setting_modal").fadeOut(400);
            }
        });
    });

    function closeModalForSystemPrompt(e) {
        let $target = $(e.target);

        // モーダル外のクリック、または特定のボタンのクリックの場合に処理
        if(!$target.closest('#system_prompt_panel').length && $('#system_prompt_panel').is(":visible") || $target.is('#close_system_prompt_panel')) {
            $('#customized_prompt').val($('#work_system_prompt').val());
            $("#system_prompt_modal").fadeOut(400);
    
            // ハンドラを削除
            $(document).off('click', '#save_system_prompt');
            $(document).off('click', '#undo_by_default');
            $(document).off('click', '#undo_by_saved');
            $(document).off('click', closeModalForSystemPrompt);
        }
    }
    $('#customize-system-prompt').click(function(event){
        event.stopPropagation();
        $('#work_system_prompt').val($('#customized_prompt').val());
        $('#undo_by_default').show();
        $("#system_prompt_modal").fadeIn(400);
    
        // 名前付き関数を使ってハンドラを設定
        $(document).on('click', '#save_system_prompt', saveSystemPromptHandler);
        $(document).on('click', '#undo_by_default', undoByDefault);
        $(document).on('click', '#undo_by_saved', undoBySaved);
        $(document).on('click', closeModalForSystemPrompt);
    });

    if ('prompt_content' in user_prompt) {
        $('#saved_user_prompt').val(user_prompt.prompt_content);
        $('#user_prompt_revision').val(user_prompt.revision);
    } else {
        $('#saved_user_prompt').val("");
        $('#user_prompt_revision').val("0");
    }

    function getUserPrompt(chat_uuid, func) {
        // Ajaxでシステムプロンプトを取得する。
        $.ajax({
            url: REMOTE_URL + '/chat_history/user_prompt',
            type: 'GET',
            contentType: 'application/json',
            data: { chat_uuid: chat_uuid },
            dataType: 'json',
            success: function(data) {
                // Assume that 'data' is an object and we want to extract 'content' from it
                var result = data.result;
                var prompt_content = data.prompt_content;
                var user_prompt_revision = data.user_prompt_revision;
                if (result !== true) {
                    console.log("result is not true. data=" + JSON.stringify(data, null, 2));  // This will print the data as a nicely formatted JSON string
                }

                $('#saved_user_prompt').val(prompt_content);
                $('#user_prompt_revision').val(user_prompt_revision);
                func(prompt_content);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                //#contents_field
                let undoLastChat = true;    // 送信したメッセージをテキストエリアに戻すか
                if (textStatus === 'timeout') {
                    console.error('Request timed out');
                    // タイムアウト処理
                    showWarningMessage('リクエストがタイムアウトしました。', 5000);
                } else if (textStatus === 'parsererror') {
                    console.error('Failed to parse JSON');
                    // JSON解析エラーの処理
                    showWarningMessage('レスポンスが不正です。', 5000);
                } else if (textStatus === 'error') {
                    // その他のエラー処理
                    const response = JSON.parse(jqXHR.responseText);
                    console.error('Server responded with:', response);
                    showWarningMessage('エラーが発生しました。', 5000);
                } else {
                    console.error('Error', textStatus, errorThrown);
                    // その他のエラー処理
                    showWarningMessage('エラーが発生しました。', 5000);
                }
            }
        });
    }

    function saveUserPromptHandler(e) {
        var chat_uuid = $('#chat_uuid').val();
        var updatedContent = $('#work_system_prompt').val();
        var revision = $('#user_prompt_revision').val();
        $.ajax({
            url: REMOTE_URL + '/chat_history/user_prompt',
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'X-Chat-Url': window.location.href
            },
            data: JSON.stringify({
                'chat_uuid': chat_uuid,
                'content': updatedContent,
                'revision': revision,
            }),
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
                $('#saved_user_prompt').val(updatedContent);
                $('#user_prompt_revision').val(parseInt(revision) + 1);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error.message, 20000);
                }
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    }

    function undoBySavedForUserPromptHandler(e) {
        var chat_uuid = $('#chat_uuid').val();
        getUserPrompt(chat_uuid, function(s) { $('#work_system_prompt').val(s); });
    }
    
    function closeModalForUserPrompt(e) {
        let $target = $(e.target);

        // モーダル外のクリック、または特定のボタンのクリックの場合に処理
        if(!$target.closest('#system_prompt_panel').length && $('#system_prompt_panel').is(":visible") || $target.is('#close_system_prompt_panel')) {
            $("#system_prompt_modal").fadeOut(400);
    
            // ハンドラを削除
            $(document).off('click', '#save_system_prompt');
            // $(document).off('click', '#undo_by_default');
            $(document).off('click', '#undo_by_saved');
            $(document).off('click', closeModalForUserPrompt);
        }
    }

    $('#edit-user-prompt').click(function(event){
        event.stopPropagation();
        $('#work_system_prompt').val($('#saved_user_prompt').val());
        $('#undo_by_default').hide();
        $("#system_prompt_modal").fadeIn(400);
    
        // 名前付き関数を使ってハンドラを設定
        $(document).on('click', '#save_system_prompt', saveUserPromptHandler);
        // $(document).on('click', '#undo_by_default', undoByDefault);
        $(document).on('click', '#undo_by_saved', undoBySavedForUserPromptHandler);
        $(document).on('click', closeModalForUserPrompt);
    });

    $('#btn-word-replace-setting').click(function(event){
        event.stopPropagation();
        $("#word_replace_modal").fadeIn(400);

        // １件もテーブルに行がない場合、新規入力用に空行を１行追加する。
        if ($('#replace_pairs_form tbody').children().length === 0) {
            $('#word_replace_addRow').click();
        }

        $(document).click(function(e) {
            let $target = $(e.target);
            if(!$target.closest('#word_replace_panel').length && $('#word_replace_panel').is(":visible")) {
                $("#word_replace_modal").fadeOut(400);
            }
        });
        $(document).on('click', '#close_system_prompt_Panel', function() {
            // 親要素を探す
            const $modal = $(this).closest('#word_replace_modal');
    
            if(!$modal.closest('#word_replace_panel').length && $('#word_replace_panel').is(":visible")) {
                $("#word_replace_modal").fadeOut(400);
            }
        });
    });

    window.word_replace_row_count = 0;
    $('#word_replace_addRow').click(function(event) {
        event.preventDefault(); // ここでフォームのデフォルトのサブミット動作をキャンセル
        window.word_replace_row_count += 1;
        var newRow = $('<tr class="form-row">' +
            '<td><label><input type="radio" name="isAssistant_' + window.word_replace_row_count + '" class="is-assistant" value="user" checked>User</label>&nbsp;' +
            '<label><input type="radio" name="isAssistant_' + window.word_replace_row_count + '" class="is-assistant" value="assistant">Assistant</label>' +
            '<td><input type="text" name="keys[]" class="key-input"></td>' +
            '<td><input type="text" name="values[]" class="value-input"></td>' +
            '<td><i class="fa-solid fa-trash remove-row"></i></td>' +
            '</tr>');

        $('#replace_pairs_form tbody').append(newRow);
    });
    
    $('#replace_pairs_form table').on('click', '.remove-row', function(event) {
        event.preventDefault(); // ここでフォームのデフォルトのサブミット動作をキャンセル
        event.stopPropagation();    // イベントの伝播を止める
        $(this).closest('tr').remove();
    });

    $('#word_replace_submitForm').click(function(event) {
        event.preventDefault(); // ここでフォームのデフォルトのサブミット動作をキャンセル
        var data = $('#replace_pairs_form').serialize();
        data = data + '&chat_uuid=' + $('#chat_uuid').val();
        console.log('data=' + data);

        $.ajax({
            url: REMOTE_URL + '/chat_history/word-replace',
            type: 'POST',
            headers: {
                'X-Chat-Url': window.location.href
            },
            data: data,
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
                showSuccessMessage("Saved.", 3000);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error.message, 20000);
                }
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    });

    $('#contents_field').on('click', '.message-copy-icon', function() {

        // 親要素を探す
        const messageBlock = $(this).closest('.message-block');

        // messageBlock内の.saysクラスのHTMLを探す
        let $says = messageBlock.find('.says');
   
        // saysフィールドからメッセージを取得する。
        let textToCopy = getTextFromDiv($says);
    
        // クリップボードにテキストをコピー
        navigator.clipboard.writeText(textToCopy).then(() => {
            console.log('Text copied to clipboard');
            showSuccessMessage('Message are copied.', 2000);
        }).catch(err => {
            console.error('Error copying text to clipboard', err);
            showWarningMessage('Failed to copy a message.', 2000);
        });
    });

    // マウスが要素に重なった時のイベントをdocument上で監視します
    $(document).on("mouseenter", ".message-edit-icon", function() {
        // $(this).css('opacity', 1); // マウスが重なった要素を表示
        $(this).addClass('icon-active');
    });

    // マウスが要素から離れた時のイベントをdocument上で監視します
    $(document).on("mouseleave", ".message-edit-icon", function() {
        // $(this).css('opacity', 0); // マウスが離れた要素を非表示
        $(this).removeClass('icon-active');
    });

    // クリックされた時のイベントをdocument上で監視します
    $(document).on("click", ".user .message-resay-icon", function() {
        // 親要素を探す
        const messageBlock = $(this).closest('.message-block');
        let seq = messageBlock.attr('message-seq');
        if (seq === undefined || seq === '' || seq === '0' || !seq) {
            return;
        }

        // messageBlock内の.saysクラスのHTMLを探す
        let $says = messageBlock.find('.says');
        // saysフィールドからメッセージを取得する。
        let userText = getTextFromDiv($says);
        console.log('seq=' + seq + ', user.message=' + userText);

        // Ajaxでユーザメッセージ以降を削除する。
        var chat_uuid = $('#chat_uuid').val();
        $.ajax({
            url: REMOTE_URL + '/chat_history/' + seq,
            type: 'DELETE',
            contentType: 'application/json',
            data: JSON.stringify({ chat_uuid: chat_uuid }),
            dataType: 'json',
            success: function(data) {
                // Assume that 'data' is an object and we want to extract 'content' from it
                var result = data.result;

                if (result !== true) {
                    console.log("result is not true. data=" + JSON.stringify(data, null, 2));  // This will print the data as a nicely formatted JSON string
                }

                // クリックしたユーザメッセージ以下を画面から削除。
                let redoTimeMills = 850;
                $('div[message-seq="' + seq + '"]').nextAll('div.message-block').addBack().fadeOut(redoTimeMills, function() {
                    // このコールバックは各要素がフェードアウトを完了した後に呼び出される
                    $(this).remove();
                });
                // クリックしたユーザメッセージをテキストエリアにコピー。
                setTimeout(function() {
                    $('#content_input').val(userText).trigger('input');
                }, redoTimeMills);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                //#contents_field
                let undoLastChat = true;    // 送信したメッセージをテキストエリアに戻すか
                if (textStatus === 'timeout') {
                    console.error('Request timed out');
                    // タイムアウト処理
                    showWarningMessage('リクエストがタイムアウトしました。', 5000);
                } else if (textStatus === 'parsererror') {
                    console.error('Failed to parse JSON');
                    // JSON解析エラーの処理
                    showWarningMessage('レスポンスが不正です。', 5000);
                } else if (textStatus === 'error') {
                    // その他のエラー処理
                    const response = JSON.parse(jqXHR.responseText);
                    console.error('Server responded with:', response);
                    showWarningMessage('エラーが発生しました。', 5000);
                } else {
                    console.error('Error', textStatus, errorThrown);
                    // その他のエラー処理
                    showWarningMessage('エラーが発生しました。', 5000);
                }
            }
        });
    });

    function reloadAssistantFaceList(image_urls) {
        $('#assistant-face-list').empty();
        $.each(image_urls, function(index, url) {
            $('#assistant-face-list').append($('<img>', {src: url}).addClass('assistant-img'));
        });    
    }
    // クリックされた時のイベントをdocument上で監視します
    $(document).on("click", ".message-edit-icon.icon-active", function() {
        // 親要素を探す
        const messageBlock = $(this).closest('.message-block');
        const isUser = messageBlock.hasClass('user');
        let seq = messageBlock.attr('message-seq');
        if (seq === undefined || seq === '' || seq === '0' || !seq) {
            return;
        }
        // messageBlock内の.saysクラスのHTMLを探す
        let $says = messageBlock.find('.says');
        // saysフィールドからメッセージを取得する。
        let originalText = getTextFromDiv($says);

        var textArea = $('<textarea class="says">').val(originalText);
        $says.replaceWith(textArea);
        textArea.focus();

        // textareaでのキーイベントの検出
        textArea.on('keydown', function(e) {
            // Ctrl+Enterが押されたとき
            if ((e.metaKey || e.ctrlKey) && e.keyCode == 13) {
                var $saysTextarea = $(this);
                var updatedContent = $saysTextarea.val();
                var sendContent = updatedContent;
                if (updatedContent === '') {
                    console.warn('warn: content is empty.');
                    return;
                }

                // 親要素を探す
                const messageBlock = $(this).closest('.message-block');
                let seq = messageBlock.attr('message-seq');
                if (!seq) {
                    console.warn('warn: seq is not a valid value.');
                    return;
                }

                // ワードを置換する
                sendContent = replaceWordsClientToServer(sendContent, messageBlock.hasClass('assistant') ? 'assistant' : 'user');

                var chat_uuid = $('#chat_uuid').val();
                $.ajax({
                    url: REMOTE_URL + '/chat_history/' + seq,
                    type: 'POST',
                    contentType: 'application/json',
                    headers: {
                        'X-Chat-Url': window.location.href
                    },
                    data: JSON.stringify({
                        'chat_uuid': chat_uuid,
                        'content': sendContent
                    }),
                    dataType: 'json',
                    beforeSend: function() {
                        // リクエスト開始時にローディングアイコンを表示
                        showLoadingIcon();
                    },
                    success: function(data) {
                        var $saysDiv = $('<div class="says">').html(updatedContent.replace(/\n/g, '<br>'));
                        $saysTextarea.replaceWith($saysDiv);

                        // メッセージエリアのアイコンを設定する。
                        setSaysIcons($saysDiv, isUser);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        console.error('Error', textStatus, errorThrown);
                        if (jqXHR.responseJSON) {
                            showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error.message, 20000);
                        }
                    },
                    complete: function(jqXHR, textStatus) {
                        // 処理完了後にローディングアイコンを非表示にする
                        hideLoadingIcon();
                    }
                });
            }
            // ESCが押されたとき
            else if (e.keyCode == 27) {
                var $saysDiv = $('<div class="says">').html(originalText.replace(/\n/g, '<br>'));
                $(this).replaceWith($saysDiv);

                // メッセージエリアのアイコンを設定する。
                setSaysIcons($saysDiv, isUser);
            }
        });
        textArea.on("input", function() {
            // textareaの高さを計算して指定
            $(this).css("height", "auto");
            $(this).css("height", $(this).prop("scrollHeight") + "px");
            var divHeight = parseInt($(this).prop("scrollHeight")) + 2;
            $('.bottom-fixed').css("height", divHeight + "px");
            $('.scrollable-content').css("bottom", divHeight + "px");
        });
        textArea.trigger('input');  // textareaの初期表示時にtextareaの高さを調節する。
    });

    initCustomizeSystemPrompt();

    reloadAssistantFaceList(assistant_pic_url_list); // 画像のURLの配列

    function disabledAssistantPicSelectionButtons(flag) {
        $('#save-assistant-pic-selection').prop('disabled', flag);
        $('#apply-assistant-pic-selection').prop('disabled', flag);
        $('#release-assistant-pic-selection').prop('disabled', flag);
    }
    disabledAssistantPicSelectionButtons(true);

    $(document).on('click', '#save-assistant-pic-selection', function() {
        var chat_uuid = $('#chat_uuid').val();
        var image_url = $('#selected-image-url').val();
        $.ajax({
            url: REMOTE_URL + '/chat/assistant-image',
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'X-Chat-Url': window.location.href
            },
            data: JSON.stringify({
                'chat_uuid': chat_uuid,
                'image_url': image_url
            }),
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
                $('#apply-assistant-pic-selection').click();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error.message, 20000);
                }
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    });

    // 未セーブの顔写真のURL
    window.assistant_temp_pic_url = '';
    $(document).on('click', '#apply-assistant-pic-selection', function() {
        let image_url = $('#selected-image-url').val();
        console.log('image_url=' + image_url);
        $('.message-block .assistant-img').each(function() {
            $(this).attr('src', image_url);
        });
        window.assistant_temp_pic_url = image_url;
    });

    $(document).on('click', '#release-assistant-pic-selection', function() {
        $('.assistant-img').removeClass('selected-image'); // 他の選択を解除
        $('#selected-image-url').val('');
        window.assistant_temp_pic_url = '';

        disabledAssistantPicSelectionButtons(true);
    });

    $('#assistant-face-list').on('click', '.assistant-img', function() {
        $('.assistant-img').removeClass('selected-image'); // 他の選択を解除
        $(this).addClass('selected-image'); // クリックされた画像にクラスを追加
        $('#selected-image-url').val($(this).attr('src'));

        disabledAssistantPicSelectionButtons(false);
    });

    $('.btn-reload-face').click(function() {
        $('.assistant-img').removeClass('selected-image'); // 他の選択を解除
        $('#selected-image-url').val('');
        disabledAssistantPicSelectionButtons(false);

        $.ajax({
            url: REMOTE_URL + '/chat/assistant-image',
            type: 'GET',
            contentType: 'application/json',
            headers: {
                'X-Chat-Url': window.location.href
            },
            data: {},
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
                var url_list = data.assistant_pic_url_list;
                reloadAssistantFaceList(url_list);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error.message, 20000);
                }
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    });

    // ワード置換のテーブルを作成
    if (word_replasing_list) {
        word_replasing_list.forEach(record => {
            var role = record.role;
            var word_client = record.word_client;
            var word_server = record.word_server;
            var user_checked = "";
            var assistant_checked = "";
            if (role === "assistant") {
                assistant_checked = "checked";
            } else {
                user_checked = "checked";
            }

            window.word_replace_row_count += 1;
            var newRow = $('<tr class="form-row">' +
                '<td><label><input type="radio" name="isAssistant_' + window.word_replace_row_count + '" class="is-assistant" value="user" ' + user_checked + '>User</label>&nbsp;' +
                '<label><input type="radio" name="isAssistant_' + window.word_replace_row_count + '" class="is-assistant" value="assistant"' + assistant_checked + '>Assistant</label>' +
                '<td><input type="text" name="keys[]" class="key-input" value="' + escapeHTML(word_client) + '"></td>' +
                '<td><input type="text" name="values[]" class="value-input" value="' + escapeHTML(word_server) + '"></td>' +
                '<td><i class="fa-solid fa-trash remove-row"></i></td>' +
                '</tr>');
    
            $('#replace_pairs_form tbody').append(newRow);
        });
    }

    function generateUserChat() {
        var chat_uuid = $('#chat_uuid').val();
        var model_id = $('#select_model').val();
        var content = $('#content_input').val();
        if (content === "8" || content === "9" || content === "1001") {
            model_id = content;
        }

        $.ajax({
            url: REMOTE_URL + '/user-chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ chat_uuid: chat_uuid, model_id: model_id }),
            dataType: 'json',
            success: function(data) {
                // Assume that 'data' is an object and we want to extract 'content' from it
                var result = data.result;
                var content = data.content;

                if (result) {
                    $('#content_input').val(content).trigger('input');
                } else {
                    console.log("result is not true. data=" + JSON.stringify(data, null, 2));  // This will print the data as a nicely formatted JSON string
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                //#contents_field
                let undoLastChat = true;    // 送信したメッセージをテキストエリアに戻すか
                if (textStatus === 'timeout') {
                    console.error('Request timed out');
                    // タイムアウト処理
                    showWarningMessage('リクエストがタイムアウトしました。', 5000);
                } else if (textStatus === 'parsererror') {
                    console.error('Failed to parse JSON');
                    // JSON解析エラーの処理
                    showWarningMessage('レスポンスが不正です。', 5000);
                } else if (textStatus === 'error') {
                    // その他のエラー処理
                    const response = JSON.parse(jqXHR.responseText);
                    console.error('Server responded with:', response);
                    showWarningMessage('エラーが発生しました。', 5000);
                    // メッセージがある場合はtextareaにappendする。
                    let message = response["error"]["message"];
                    let preText = "";
                    $('#content_input').val(preText + message).trigger('input');
                } else {
                    console.error('Error', textStatus, errorThrown);
                    // その他のエラー処理
                    showWarningMessage('エラーが発生しました。', 5000);
                }
            }
        });
    };

    $('#btn_generate').on('click', function() {
        chat_send_timer = setTimeout(function() {
            if (!chat_click_prevent) {
                // クリックイベントの処理
                generateUserChat();
            }
            chat_click_prevent = false;
        }, chat_click_delay);
    }).on('dblclick', function(e) {
        clearTimeout(chat_send_timer);
        chat_click_prevent = true;

        // 現在のモデルを取得
        let current_model = document.getElementById('select_model').value;
        // モデルの選択を一時的にGPT-4に変更
        document.getElementById('select_model').value = '9';    // gpt-4-1106-preview
        // チャット処理
        generateUserChat();
        // モデルの選択を元に戻す
        document.getElementById('select_model').value = current_model;
    });

});

function playAudio(path) {
    const audio = document.querySelector("audio");
    audio.src = path; // URL.createObjectURL(path);
    audio.play();
}

function getContent() {
    var latestText = document.getElementById('content_input').value;
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

let btnSubmit = document.getElementById("btn_submit");

function clearButtonColor() {
    btnSubmit.classList.remove('moderation-color-warn', 'moderation-color-critical', 'moderation-color-ok', 'moderation-color-white', 'moderation-color-error', 'quick-change');
}

function changeBackgroundColorButton(color) {

    var colorCd = '';

    // 一旦、全ての色関連クラスをリセット
    clearButtonColor();

    // // 色を即座に変えるためのクラスを追加
    // btnSubmit.classList.add('quick-change');

    if (color === 'warn') {
        // colorCd = '#FFA580';  // オレンジ
        colorCd = 'moderation-color-warn';
    } else if (color === 'critical') {
        // colorCd = '#FFB6C1';  // 赤
        colorCd = 'moderation-color-critical';
    } else if (color === 'ok') {
        // colorCd = '#90EE90';  // 緑
        colorCd = 'moderation-color-ok';
    } else if (color === 'white') {
        // colorCd = white;  // 白。色のリセットの意味
        colorCd = 'moderation-color-white';
    } else if (color === 'error') {
        // colorCd = '#D0D0D0';  // グレー
        colorCd = 'moderation-color-error';
    } else {
        return;
    }

    // 色を変える
    btnSubmit.classList.add(colorCd);

    // // 0.01秒後にquick-changeクラスを取り除く
    // setTimeout(() => {
    //     btnSubmit.classList.remove('quick-change');
    // }, 10);

    // // 4秒後に背景色を白に戻す
    // setTimeout(function() {
    //     btnSubmit.classList.remove('moderation-color-warn', 'moderation-color-critical', 'moderation-color-ok', 'moderation-color-error');
    // }, 4000);
}

var checkModerationNow = false;

async function getModerationResult() {
    let result = false;
    // // テキストエリアを白くする
    // changeBackgroundColorTextarea('reset');

    var content = getContent();
    var csrf_token = "";  // $('#csrf_token').val();
    var moderation_model_no = "1";

    if (content === '') {
        return;
    }

    // リクエスト開始時にローディングアイコンを表示
    showLoadingIcon();

    try {
        let response = await fetch(REMOTE_URL + '/moderation/check-for-chat', {
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
        });

        let data = await response.json();
        if (!response.ok) {
            throw new Error(json.error_message || 'Unknown error');
        }

        var done = false;
        if (data && data.result_val) {
            if (data.result_val === 'orange') {
                changeBackgroundColorButton('warn');
                done = true;
                checkModerationNow = true;
            } else if (data.result_val === 'red') {
                changeBackgroundColorButton('critical');
                done = true;
            } else if (data.result_val === 'ok') {
                changeBackgroundColorButton('ok');
                done = true;
                result = true;
                checkModerationNow = true;
            }
        }
        if (!done) {
            changeBackgroundColorButton('error');
        }

    } catch (error) {
        console.error('Error:', error.message);
        changeBackgroundColorButton('error');
    } finally {
        // ローディングアイコンを非表示にする
        hideLoadingIcon();
    }

    return result;
}

async function submitToServer(continueFlag = false) {
    // if (!checkModerationNow) {
    //     // 現在の内容でモデレーションをしていなければ実行
    //     let modResult = await getModerationResult();
    //     if (!modResult) {   // モデレーションに失敗した場合はchatを送らない
    //         // checkModerationNow = true;
    //         // このフラグはgetModerationResult()内で立てる。
    //         return;
    //     }
    // }

    var inputText = $('#content_input').val().trim();
    var sendText = inputText;
    var chat_name = $('#chat_name').val();
    var chat_uuid = $('#chat_uuid').val();
    var model_id = $('#select_model').val();
    var system_prompt = $('#customized_prompt').val();
    if (inputText === "" && !continueFlag) {
        $('#content_input').focus();
        return;
    }
    $('#content_input').val("").trigger('input');
    $('#content_input').focus();
    if (!continueFlag) {
        appendContent(inputText, 'user');
        sendText = replaceWordsClientToServer(sendText, 'user');
    }

    console.log("#audioOn=" + $('#audioOn').prop('checked'));

    $.ajax({
        url: REMOTE_URL + '/chat2',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ chat_uuid: chat_uuid, chat_name: chat_name, content: sendText, model_id: model_id, system_prompt: system_prompt,
            continueFlag: continueFlag,
            audioOn: $('#audioOn').prop('checked') ? '1' : '0',
            is_summary_enabled: $('#summarizeOn').prop('checked') ? '1' : '0',
            speaker: $('#audioCredit').val() }),
        dataType: 'json',
        success: function(data) {
            // Assume that 'data' is an object and we want to extract 'content' from it
            var result = data.result;
            var role = data.role;
            var content = data.content;
            var audioPath = data.audio_path;
            var chatName = data.chat_name;
            var image_url = data.image_url;
            var user_seq = data.user_seq;
            var assistant_seq = data.assistant_seq;
            var model_name = data.model_name;
            let user_moderation = "";
            let assistant_moderation = "";

            // モデレーション結果を取得する
            if ("moderation_result" in data) {
                if (data.moderation_result.length >= 2) {    // Sayの場合
                    user_moderation = data.moderation_result[0];
                    assistant_moderation = data.moderation_result[1];
                } else if (data.moderation_result.length == 1) {    // Continueの場合
                    assistant_moderation = data.moderation_result[0];
                }
            }

            if (!continueFlag) {
                let target = $('#contents_field>.message-block:last');
                target.attr('message-seq', user_seq);
                if (user_moderation !== "") {
                    if (user_moderation === "O") {
                        target.addClass('warning');
                    }
                    else if (user_moderation === "R") {
                        target.addClass('critical');
                    }
                }
            } else {
                // 続きの場合は、既存の最後のassistantのチャットを削除する
                let target = $('#contents_field>.message-block:last');
                target.remove();
            }

            appendContent(content, role, true, window.assistant_temp_pic_url !== '' ? window.assistant_temp_pic_url : image_url, assistant_moderation, assistant_seq, model_name);
            changeBackgroundColorButton('ok');
            if (audioPath !== null) {
                playAudio(REMOTE_URL + audioPath);
            }
            if (result !== true) {
                console.log("result is not true. data=" + JSON.stringify(data, null, 2));  // This will print the data as a nicely formatted JSON string
            }
            if (chatName) {
                $('#chat_name').val(chatName);
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //#contents_field
            let undoLastChat = true;    // 送信したメッセージをテキストエリアに戻すか
            if (textStatus === 'timeout') {
                console.error('Request timed out');
                // タイムアウト処理
                showWarningMessage('リクエストがタイムアウトしました。', 5000);
            } else if (textStatus === 'parsererror') {
                console.error('Failed to parse JSON');
                // JSON解析エラーの処理
                showWarningMessage('レスポンスが不正です。', 5000);
            } else if (textStatus === 'error') {
                if(jqXHR.status == 400 && jqXHR.responseJSON && jqXHR.responseJSON.error && jqXHR.responseJSON.error.code === 'moderation') {

                    let moderation_result = jqXHR.responseJSON.error.details.result;
                    if (moderation_result === 'orange') {
                        changeBackgroundColorButton('warn');
                    } else if (moderation_result === 'red') {
                        changeBackgroundColorButton('critical');
                        undoLastChat = false;
                    } else {
                        changeBackgroundColorButton('error');
                    }
                    
                } else {
                    // その他のエラー処理
                    const response = JSON.parse(jqXHR.responseText);
                    console.error('Server responded with:', response);
                    showWarningMessage('エラーが発生しました。', 5000);
                    // メッセージがある場合はtextareaにappendする。
                    let message = response["error"]["message"];
                    let preText = inputText;
                    if (preText !== "") preText = preText + "\n";
                    $('#content_input').val(preText + message).trigger('input');
                }
            } else {
                console.error('Error', textStatus, errorThrown);
                // その他のエラー処理
                showWarningMessage('エラーが発生しました。', 5000);
            }

            if (!continueFlag) {
                $("#contents_field>div.message-block:last-child").fadeOut(1000, function() {
                    $(this).remove();

                    if (undoLastChat) {
                        $('#content_input').val(inputText).trigger('input');
                    } else {
                        setTimeout(function() {
                            btnSubmit.classList.add('slow-change-300ms');
                            changeBackgroundColorButton('white');
                            setTimeout(function() {
                                btnSubmit.classList.remove('slow-change-300ms');
                                btnSubmit.classList.add('slow-change-1s');
                                changeBackgroundColorButton('ok');
                            }, 300);
                            setTimeout(function() {
                                btnSubmit.classList.remove('slow-change-1s');
                            }, 1500);
                        }, 2000);
                    }
                });
            }
        }
    });
}

$('#content_input').keydown(function(event) {
    if ((event.metaKey || event.ctrlKey) && event.keyCode == 13) {
        // Ctrl + Enterが押された時の処理
        $('#btn_submit').click();  // '送信' ボタンのclickイベントをトリガーする
    }
});

var chat_send_timer = 0;
var chat_click_delay = 200;
var chat_click_prevent = false;

$('#btn_submit').on('click', function() {
    chat_send_timer = setTimeout(function() {
        if (!chat_click_prevent) {
            // クリックイベントの処理
            submitToServer();
        }
        chat_click_prevent = false;
    }, chat_click_delay);
}).on('dblclick', function(e) {
    clearTimeout(chat_send_timer);
    chat_click_prevent = true;

    // 現在のモデルを取得
    let current_model = document.getElementById('select_model').value;
    // モデルの選択を一時的にGPT-4に変更
    document.getElementById('select_model').value = '9';    // gpt-4-1106-preview
    // チャット処理
    submitToServer();
    // モデルの選択を元に戻す
    document.getElementById('select_model').value = current_model;
});

$('#btn_continue').on('click', function() {
    chat_send_timer = setTimeout(function() {
        if (!chat_click_prevent) {
            // クリックイベントの処理
            submitToServer(true);
        }
        chat_click_prevent = false;
    }, chat_click_delay);
}).on('dblclick', function(e) {
    clearTimeout(chat_send_timer);
    chat_click_prevent = true;

    // 現在のモデルを取得
    let current_model = document.getElementById('select_model').value;
    // モデルの選択を一時的にGPT-4に変更
    document.getElementById('select_model').value = '9';    // gpt-4-1106-preview
    // チャット処理
    submitToServer(true);
    // モデルの選択を元に戻す
    document.getElementById('select_model').value = current_model;
});

function setupNewChatUUID(chat_uuid = '') {
    if (chat_uuid === '') {
        chat_uuid = mkuuid();
    }
    $('#chat_uuid').val(chat_uuid);
    var newURL = REMOTE_URL + '/?chat_uuid=' + chat_uuid;
    history.pushState(null, null, newURL);
}

$('#btn_newchat').click(function() {
    $('#chat_name').val('');
    $('#contents_field').empty();

    setupNewChatUUID();

    // ブラウザを再読み込みする。
    window.location.reload();
});

if (!document.location.href.includes('/?chat_uuid=')) {
    setupNewChatUUID($('#chat_uuid').val());
}

$('#copy-assistant-message').click(function(){
    // テキストを連結するための変数を初期化
    var concatenatedText = '';

    // .message-block.assistant クラスを持つ全ての要素に対して処理を行う
    $('.message-block.assistant').each(function() {
        // .says クラスの子要素を取得
        var $says = $(this).find('.says');

        // 取得した要素からテキストを取得し、連結する
        concatenatedText += getTextFromDiv($says) + '\n'; // 改行で区切る
    });

    // クリップボードにテキストをコピー
    navigator.clipboard.writeText(concatenatedText).then(() => {
        console.log('Text copied to clipboard');
        showSuccessMessage('Assistant messages are copied.', 1000);
    }).catch(err => {
        console.error('Error copying text to clipboard', err);
        showWarningMessage('Failed to copy Assistant messages.', 2000);
    });
});

$('#copy-all-message').click(function(){
    // テキストを連結するための変数を初期化
    var concatenatedText = '';

    // .message-block.assistant クラスを持つ全ての要素に対して処理を行う
    $('.message-block').each(function() {
        // .says クラスの子要素を取得
        var $says = $(this).find('.says');

        // 取得した要素からテキストを取得し、連結する
        concatenatedText += getTextFromDiv($says) + '\n'; // 改行で区切る
    });

    // クリップボードにテキストをコピー
    navigator.clipboard.writeText(concatenatedText).then(() => {
        console.log('Text copied to clipboard');
        showSuccessMessage('All messages are copied.', 1000);
    }).catch(err => {
        console.error('Error copying text to clipboard', err);
        showWarningMessage('Failed to copy all message.', 2000);
    });
});
