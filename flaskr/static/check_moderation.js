$(document).ready(function() {
    window.simplemde;

    window.check_moderation = function() {
        var content = simplemde.value().trim();
        var csrf_token = $('#csrf_token').val();
        var moderation_model_no = $('input[name="moderation-model"]:checked').val();
    
        if (content === '') {
            return;
        }
        $.ajax({
            url: REMOTE_URL + '/moderation/check',
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'X-Chat-Url': window.location.href
            },
            data: JSON.stringify({
                'content': content,
                'moderation_model_no': moderation_model_no,
                'csrf_token': csrf_token
            }),
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
                var div = $('#moderation_panel');
                if (div.length > 0) {
                    div.remove();
                }
                var moderationPanel = $('<div id="moderation_panel"></div>');
                moderationPanel.append(createModerationTable(data));
                $('#detail_panel').prepend(moderationPanel);
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
    
    $('#download_by_text_button').click(function() {
        downloadPrompt(".txt");
    });

    $('#download_by_md_button').click(function() {
        downloadPrompt(".md");
    });

    $('#copy_to_clipboard_button').click(copy_to_clipboard);

    $('#check_moderation').click(function() {
        check_moderation();

        // 画面の一番上にスクロール
        $('html, body').animate({
            scrollTop: 0
        }, 800);  // 800ミリ秒（0.8秒）かけてスクロールさせる
    });

    $('#remove_wastes').click(function() {
        var text = simplemde.value();
        var removeWords = [/^ChatGPT\s*(!\s*)?/gm, /^User!?\s*/gm, /^Save & Submit\s*/gm, /^Cancel\s*/gm, /^\s*/gm, /^\d+ \/ \d+\s*/gm, /^This content may violate our content policy.*\s*/gm];
        for (var i = 0; i < removeWords.length; i++) {
            text = text.replace(removeWords[i], '');
        }
        simplemde.value(text);
    });

    $('.prompt_editor').each(setup_prompt_editor);

    // 翻訳データを取得する（非同期）
    get_translation_data();
});