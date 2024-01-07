$(document).ready(function() {
    $('#login_button').click(function(e) {
        e.preventDefault();  // ボタンのデフォルトの動作を停止

        // エラーメッセージがあれば消す
        $('#invalidate_login_id').html('&nbsp; ');
        $('#invalidate_password').html('&nbsp; ');

        var login_id = $('#login_id').val().trim();
        var password = $('#password').val().trim();
        var next = $('#next').val().trim();
        var csrf_token = $('#csrf_token').val();

        if (next === "None") {
            next = "";
        }

        // 入力チェック
        var validate = true;
        if (login_id === '') {
            $('#invalidate_login_id').text('Input login id.');
            validate = false;
        }
        if (password === '') {
            $('#invalidate_password').text('Input password.');
            validate = false;
        }
        if (!validate) {
            return;
        }

        $.ajax({
            url: REMOTE_URL + '/login',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                'login_id': login_id,
                'password': password,
                'next': next,
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
                $('#main_error_message').text(jqXHR.responseJSON.main_error_message);
                $('#invalidate_login_id').text(jqXHR.responseJSON.login_id);
            }
        });
    });

    $('#register_user_button').click(function(e) {
        e.preventDefault();  // ボタンのデフォルトの動作を停止

        // エラーメッセージがあれば消す
        $('#invalidate_login_id').html('&nbsp; ');
        $('#invalidate_password').html('&nbsp; ');
        $('#invalidate_user_name').html('&nbsp; ');

        var login_id = $('#login_id').val().trim();
        var password = $('#password').val().trim();
        var user_name = $('#user_name').val().trim();
        var csrf_token = $('#csrf_token').val();

        // 入力チェック
        var validate = true;
        if (login_id === '') {
            $('#invalidate_login_id').text('Input login id.');
            validate = false;
        }
        if (password === '') {
            $('#invalidate_password').text('Input password.');
            validate = false;
        }
        if (user_name === '') {
            $('#invalidate_user_name').text('Input user name.');
            validate = false;
        }
        if (!validate) {
            return;
        }

        $.ajax({
            url: REMOTE_URL + '/register_user',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                'login_id': login_id,
                'password': password,
                'user_name': user_name,
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
                    if (jqXHR.responseJSON.login_id !== undefined) {
                        $('#invalidate_login_id').text(jqXHR.responseJSON.login_id);
                    }
                    if (jqXHR.responseJSON.password !== undefined) {
                        $('#invalidate_password').text(jqXHR.responseJSON.password);
                    }
                    if (jqXHR.responseJSON.user_name !== undefined) {
                        $('#invalidate_user_name').text(jqXHR.responseJSON.user_name);
                    }
                }
            }
        });
    });
});
