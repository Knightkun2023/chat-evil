$(document).ready(function() {
    window.simplemde;

    window.check_moderation = function() {
        var content = simplemde.value().trim();
        var csrf_token = $('#csrf_token').val();
        var moderation_model_no = '1';
    
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
                moderationPanel.append(createModerationTable(data, false));
                $('#moderation_modal').append(moderationPanel);
    
                $("#moderation_modal").fadeIn(400);
    
                $(document).click(function(event) {
                    let $target = $(event.target);
                    if(!$target.closest('#moderation_panel').length && $('#moderation_panel').is(":visible")) {
                        $("#moderation_modal").fadeOut(400);
                    }
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    showWarningMessage(jqXHR.status + ': ' + jqXHR.responseJSON.error_message, 20000);
                }
            },
            complete: function(jqXHR, textStatus) {
                // 処理完了後にローディングアイコンを非表示にする
                hideLoadingIcon();
            }
        });
    }
    
    $('.prompt_editor').each(setup_prompt_editor);

    $('#paste_prompt_content').click(paste_prompt_content);

    $('#delete_prompt_content').click(delete_prompt_content);

    function set_from_json(data) {
        $('#prompt_name').val(data.SystemPrompts.prompt_name);
        simplemde.value(data.SystemPrompts.prompt_content);
        if (data.is_owner && data.SystemPrompts.is_edit_locked) {
            $('#is_edit_locked').prop('checked', true);
        } else {
            $('#is_edit_locked').prop('checked', false);
        }
        if (data.SystemPrompts.is_viewable_by_everyone) {
            $('#is_viewable_by_everyone').prop('checked', true);
        } else {
            $('#is_viewable_by_everyone').prop('checked', false);
        }
        if (data.SystemPrompts.is_editable_by_everyone) {
            $('#is_editable_by_everyone').prop('checked', true);
        } else {
            $('#is_editable_by_everyone').prop('checked', false);
        }
        if (data.SystemPrompts.role_no == 1) {
            $('#role_no_user').prop('checked', true);
        } else {
            $('#role_no_assistant').prop('checked', true);
        }
    }
    function set_readonly(data, is_readonly) {
        if (is_readonly || data.is_owner) {
            $('#prompt_name').attr('readonly', is_readonly);
            $('#is_edit_locked').attr('readonly', is_readonly);
        }
//        simplemde.value(data.prompt.prompt_content);
        $('#is_viewable_by_everyone').attr('readonly', is_readonly);
        $('#is_editable_by_everyone').attr('readonly', is_readonly);
    }

    function init_data_set() {
        if ('SystemPrompts' in detail_data) {
            set_from_json(detail_data);
            set_readonly(detail_data, true);
        }
    }
    init_data_set();

    $('#revert_button').click(function() {
        init_data_set();
    });

    $('#register_button').click(function(e) {
        e.preventDefault();  // ボタンのデフォルトの動作を停止
        var isRegister = $(this).hasClass('register');
        if (!isRegister) {
            // 編集ボタン押下
            // 入力項目を編集可能にする処理
            set_readonly(detail_data, false);
            $(this).addClass('register');
            return;  // 編集可能にしたのち、ここは抜ける
        }

        // エラーメッセージがあれば消す
        $('#main_error_message').html('&nbsp; ');
        $('#invalidate_prompt_name').html('&nbsp; ');
        $('#invalidate_prompt_content').html('&nbsp; ');

        var prompt_name = $('#prompt_name').val().trim();
        var prompt_content = simplemde.value();
        var role_no = $('#role_no_user') ? ($('#role_no_user').prop('checked') ? "1": "2") : "2";
        var is_edit_locked = $('#is_edit_locked') ? ($('#is_edit_locked').prop('checked') ? "1": "0") : "0";
        var is_viewable_by_everyone = $('#is_viewable_by_everyone') ? ($('#is_viewable_by_everyone').prop('checked') ? "1": "0") : "0";
        var is_editable_by_everyone = $('#is_editable_by_everyone') ? ($('#is_editable_by_everyone').prop('checked') ? "1": "0") : "0";
        var prompt_id = '0';
        var revision = '0';
        var updated_time = '0';
        if ('SystemPrompts' in detail_data) {
            prompt_id = $('#prompt_id').val().trim();
            revision = $('#revision').val().trim();
            updated_time = $('#updated_time').val().trim();
        }
        var csrf_token = $('#csrf_token').val().trim();

        // 入力チェック
        var validate = true;
        if (prompt_name === '') {
            $('#invalidate_prompt_name').text('Input prompt name.');
            validate = false;
        }
        if (!validate) {
            return;
        }

        $.ajax({
            url: REMOTE_URL + '/prompt/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                'prompt_name': prompt_name,
                'prompt_content': prompt_content,
                'role_no': role_no,
                'is_edit_locked': is_edit_locked,
                'is_viewable_by_everyone': is_viewable_by_everyone,
                'is_editable_by_everyone': is_editable_by_everyone,
                'prompt_id': prompt_id,
                'revision': revision,
                'updated_time': updated_time,
                'csrf_token': csrf_token
            }),
            dataType: 'json',
            success: function(data) {
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    console.error('Warning: You cannot redirect.');
                    $('#main_error_message').text("You don't be allowed.");
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error', textStatus, errorThrown);
                if (jqXHR.responseJSON) {
                    if (jqXHR.responseJSON.main_error_message !== undefined) {
                        $('#main_error_message').text(jqXHR.responseJSON.main_error_message);
                    }
                    if (jqXHR.responseJSON.prompt_name !== undefined) {
                        $('#invalidate_prompt_name').text(jqXHR.responseJSON.prompt_name);
                    }
                    if (jqXHR.responseJSON.prompt_content !== undefined) {
                        $('#invalidate_prompt_content').text(jqXHR.responseJSON.prompt_content);
                    }
                }
            }
        });
    });

    $('#download_by_text_button').click(function() {
        downloadPrompt(".txt");
    });

    $('#download_by_md_button').click(function() {
        downloadPrompt(".md");
    });

    $('#copy_to_clipboard_button').click(copy_to_clipboard);

    $('#delete_button').click(function() {
        // infoメッセージボックスのOKボタン
        $('.ok').click(function() {
            var prompt_id = $('#prompt_id').val();
            var revision = $('#revision').val();
            var updated_time = $('#updated_time').val();
            var csrf_token = $('#csrf_token').val();
            $.ajax({
                url: REMOTE_URL + '/prompt/delete',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    'prompt_id': prompt_id,
                    'revision': revision,
                    'updated_time': updated_time,
                    'csrf_token': csrf_token
                }),
                dataType: 'json',
                success: function(data) {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        console.error('Warning: You cannot redirect.');
                        $('#main_error_message').text("You don't be allowed.");
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    console.error('Error', textStatus, errorThrown);
                    if (jqXHR.responseJSON) {
                        if (jqXHR.responseJSON.main_error_message !== undefined) {
                            $('#main_error_message').text(jqXHR.responseJSON.main_error_message);
                        }
                    }
                }
            });
        });

        showInfoMessage('削除してよろしいですか？', 0);
    });

    $('#check_moderation').click(check_moderation);
});