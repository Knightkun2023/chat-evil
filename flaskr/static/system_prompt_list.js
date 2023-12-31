$(document).ready(function() {
    $('.detail_button').click(function() {
        window.location = REMOTE_URL + '/prompt/' + $(this).attr('prompt_id')
    });
});
