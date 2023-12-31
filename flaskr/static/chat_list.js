$(document).ready(function() {
    function appendChatInfo($div, chat_uuid, chat_name, content = '', chat_time = '') {
        // チャット情報のレコード
        let $record_div = $('<div>', {
            class: 'chat-record',
            uuid: chat_uuid
        });
        // チャットリンクとボタンを含む領域
        let $link_div = $('<div>', {
            class: 'chat-link-record'
        });
        // ボタンを配置する領域
        let $chat_buttons = $('<div>', {
            class: 'chat-buttons'
        });

        // // チャット名をspanでおく
        // let $chatName = $('<span>', {
        //     class: 'chat-name',
        //     text: chat_name
        // });

        // 新しいaタグを作成
        let $link = $('<a>', {
            href: REMOTE_URL + '/?chat_uuid=' + chat_uuid,
            text: chat_name,
            class: 'chat-name',
            title: content.replace(/\r?\n/g, "").substring(0, 50),
            target: '_blank',
            rel: 'noopener noreferrer'
        })/*.append($chatName)*/;

        // 新しいspanタグを作成し、中にaタグを追加。さらに'chat-name'と'highlight'クラスを追加
        let $span = $('<span>', {
            class: 'chat-link'
        }).append($link);

        // チャット名のspanタグにチャット時間を追加
        if (chat_time.length === 17) {
            let chatTimeView = chat_time.substring(0, 4)
                 + '/' + chat_time.substring(4, 6)
                 + '/' + chat_time.substring(6, 8)
                 + ' ' + chat_time.substring(8, 10)
                 + ':' + chat_time.substring(10, 12)
                 + ':' + chat_time.substring(12, 14);
            let $chatTimeSpan = $('<span>', {
                class: 'chat-time',
                text: chatTimeView
            });
            $span.append($chatTimeSpan);
        }
        $link_div.append($span);

        // チャット名編集ボタン
        let $editBtn = $('<button>', {
            class: 'chat-edit',
            submit: false,
            text: "編集"
        });
        $chat_buttons.append($editBtn);
        // チャット削除ボタン
        let $deleteBtn = $('<button>', {
            class: 'chat-delete',
            submit: false,
            text: "削除"
        });
        $chat_buttons.append($deleteBtn);

        $link_div.append($chat_buttons);

        // チャットの内容のdiv領域
        let $chat_content = $('<div>', {
            class: 'chat-content',
            html: content.substring(0, 100).replace(/\r?\n/g, "<br>")
        });

        $record_div.append($link_div);
        $record_div.append($chat_content);

        $div.append($record_div);
    }

    // チャット履歴を表示させる。
    if (chat_list && chat_list.length > 0) {
        $('#chat_list_area div.empty-message').remove();

        let item = null;
        let $div = $('#chat_list_area');
        for (var i = 0; i < chat_list.length; i++) {
            item = chat_list[i];
            appendChatInfo($div, item.chat_uuid, item.chat_name, item.content, item.chat_time);
        }
    }

    $('.chat-link-record button.chat-edit').click(function() {
        // クリックされたボタンから親のdiv.chat-recordを取得
        let $chatRecord = $(this).closest('div.chat-record[uuid]');
        let chat_uuid = $chatRecord.attr('uuid');

        // そのdiv.chat-record内のspan.chat-nameを取得
        let $chatName = $chatRecord.find('a.chat-name');
        let text = $chatName.text();
        let $input = $('<input type="text" class="chat-name-edit">').val(text);
        $chatName.replaceWith($input);
        $input.focus();
        let newText = text;

        // inputでEnterキーを押したときの処理
        $input.keyup(function(e) {
            if (e.key === 'Enter') {
                newText = $input.val();
                $.ajax({
                    url: REMOTE_URL + '/chat/name',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ chat_uuid: chat_uuid, chat_name: newText }),
                    dataType: 'json',
                    beforeSend: function() {
                        // リクエスト開始時にローディングアイコンを表示
                        showLoadingIcon();
                    },
                    success: function(data) {
                        // pass
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        console.error('Error', textStatus, errorThrown);
                        // その他のエラー処理
                        showWarningMessage('エラーが発生しました。', 5000);

                        return false;
                    },
                    complete: function(jqXHR, textStatus) {
                        // 処理完了後にローディングアイコンを非表示にする
                        hideLoadingIcon();
                    }
                });
            }
            else if (e.keyCode === 27) {    // ESCキー（編集のキャンセル）
                // pass
            }
            else {
                return false;
            }

            let $chatContent = $chatRecord.find('div.chat-content');
            // 新しいaタグを作成
            let $link = $('<a>', {
                href: REMOTE_URL + '/?chat_uuid=' + chat_uuid,
                text: newText,
                class: 'chat-name',
                title: $chatContent.text(),
                target: '_blank',
                rel: 'noopener noreferrer'
            })/*.append($chatName)*/;

            $input.replaceWith($link);
        });
    });
    $('.chat-link-record button.chat-delete').click(function() {
        let $chatRecord = $(this).closest('div.chat-record[uuid]');
        let chat_uuid = $chatRecord.attr('uuid');

        $.ajax({
            url: REMOTE_URL + '/chat/delete',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ chat_uuid: chat_uuid }),
            dataType: 'json',
            beforeSend: function() {
                // リクエスト開始時にローディングアイコンを表示
                showLoadingIcon();
            },
            success: function(data) {
                $chatRecord.css('background-color', 'lightgray');
                $chatRecord.fadeOut(1000, function() {
                    $(this).remove();
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                // その他のエラー処理
                showWarningMessage('エラーが発生しました。', 5000);
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    });
});
