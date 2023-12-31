$(document).ready(function() {
    $('#register_button').click(function(e) {
        e.preventDefault();  // ボタンのデフォルトの動作を停止

        // エラーメッセージがあれば消す
        $('#invalidate_registration_code').html('&nbsp; ');
        $('#invalidate_remarks').html('&nbsp; ');
        $('#invalidate_expiration_time').html('&nbsp; ');
        $('#invalidate_roles').html('&nbsp; ');

        var registration_code = $('#registration_code').val().trim();
        var remarks = $('#remarks').val().trim();
        var expiration_time = $('#expiration_time').val().trim();
        var roles = $('#roles').val().trim();
        var csrf_token = $('#csrf_token').val();

        // 入力チェック
        var validate = true;
        if (remarks === '') {
            $('#invalidate_remarks').text('Input Remarks.');
            validate = false;
        }
        if (!validate) {
            return;
        }

        $.ajax({
            url: REMOTE_URL + '/registration_code',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                'registration_code': registration_code,
                'remarks': remarks,
                'expiration_time': expiration_time,
                'roles': roles,
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
                    if (jqXHR.responseJSON.registration_code !== undefined) {
                        $('#invalidate_registration_code').text(jqXHR.responseJSON.registration_code);
                    }
                    if (jqXHR.responseJSON.remarks !== undefined) {
                        $('#invalidate_remarks').text(jqXHR.responseJSON.remarks);
                    }
                    if (jqXHR.responseJSON.expiration_time !== undefined) {
                        $('#invalidate_expiration_time').text(jqXHR.responseJSON.expiration_time);
                    }
                    if (jqXHR.responseJSON.roles !== undefined) {
                        $('#invalidate_roles').text(jqXHR.responseJSON.roles);
                    }
                }
            }
        });
    });
});
