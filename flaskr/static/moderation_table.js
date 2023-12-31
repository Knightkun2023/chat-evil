// テーブルを作成する関数
function createModerationTable(data, addDetail = true) {
    if (Array.isArray(data.results) && data.results.length > 0) {
        var categories = data.results[0].categories;
        var categoryKeys = Object.keys(categories).sort(); // キーをアルファベット順にソート

        var table = $("<table></table>");
        var tableHeader = $("<tr><th>Category</th><th>Flag</th><th>Score</th></tr>");
        table.append(tableHeader); // ヘッダー行をテーブルに追加
    
        for (var i = 0; i < categoryKeys.length; i++) {
            var category = categoryKeys[i];
            var flagged = categories[category];
            var score = data.results[0].category_scores[category];

            var category_label = '<b>' + category + '</b><br>';
            if (addDetail) {
                if (category === 'harassment') {
                    category_label += gettext('Content that expresses, incites, or promotes harassing language towards any target.');
                } else if (category === 'harassment/threatening') {
                    category_label += gettext('Harassment content that also includes violence or serious harm towards any target.');
                } else if (category === 'hate') {
                    category_label += gettext('Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g., chess players) is harrassment.');
                } else if (category === 'hate/threatening') {
                    category_label += gettext('Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.');
                } else if (category === 'self-harm') {
                    category_label += gettext('Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.');
                } else if (category === 'self-harm/intent') {
                    category_label += gettext('Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders.');
                } else if (category === 'self-harm/instructions') {
                    category_label += gettext('Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts.');
                } else if (category === 'sexual') {
                    category_label += gettext('Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).');
                } else if (category === 'sexual/minors') {
                    category_label += gettext('Sexual content that includes an individual who is under 18 years old.');
                } else if (category === 'violence') {
                    category_label += gettext('Content that depicts death, violence, or physical injury.');
                } else if (category === 'violence/graphic') {
                    category_label += gettext('Content that depicts death, violence, or physical injury in graphic detail.');
                }
            }
            var score_class = '';
            if (score >= 0.8) {
                score_class = ' class="bg_red"';
            } else if (score >= 0.5) {
                score_class = ' class="bg_orange"';
            } else if (score >= 0.3) {
                score_class = ' class="bg_yellow"';
            }
//            var tableRowData = $("<tr " + score_class + "><td>" + category + "</td><td>" + category_label + "</td><td>" + flagged + "</td><td>" + formatNumber(score) + "</td></tr>");
            var flaggedText = flagged ? '<b>true</b>' : 'false';
            var tableRowData = $("<tr" + score_class + "><td>" + category_label + "</td><td>" + flaggedText + "</td><td>" + formatNumber(score) + "</td></tr>");
            table.append(tableRowData); // 各カテゴリの行をテーブルに追加
        }
    
        return table;
    }
    // data.results が存在しなかった場合
    var pre = $('<pre></pre>');
    pre.text(JSON.stringify(data, null, 2));
    var div_json = $('<div>' + gettext('Unable to retrieve the correct data.') + '</div>');
    div_json.append(pre);
    return div_json;
}

function paste_prompt_content() {
    navigator.clipboard.readText()
        .then(function(clipboardContent) {
            simplemde.value(clipboardContent);
        })
        .catch(function(error) {
            console.error('Failed to read clipboard content: ', error);
        });
}

function delete_prompt_content() {
    simplemde.value('');
    simplemde.codemirror.focus();
}

function downloadPrompt(ext) {
    var text = simplemde.value();
    var blob = new Blob([text], { type: "text/plain" });
    var link = document.createElement("a");
    var title = "moderated_prompt";
    link.download = title + "_" + getCurrentDateTime() + ext;
    link.href = window.URL.createObjectURL(blob);
    link.click();
}

function copy_to_clipboard() {
    navigator.clipboard.writeText(simplemde.value())
        .then(function() {
            showSuccessMessage('Prompt copied to Clipboard successfully.', 2000);
        })
        .catch(function(err) {
            showWarningMessage('Failed to copy prompt to Clipboard.', 4000);
        });
}

function downloadPrompt(ext) {
    var text = simplemde.value();
    var blob = new Blob([text], { type: "text/plain" });
    var link = document.createElement("a");
    var title = $('#prompt_name').val().trim();
    if (title === '') {
        title = "System_Prompt";
    }
    link.download = title + "_" + getCurrentDateTime() + ext;
    link.href = window.URL.createObjectURL(blob);
    link.click();
}

function setup_prompt_editor() {
    // var simplemde = new SimpleMDE({
    simplemde = new SimpleMDE({
        spellChecker: false,
        shortcuts: {},
        element: this,
        toolbar: [
            {
                name: "moderation",
                action: check_moderation,
                className: "fa-brands fa-searchengin",
                title: "Moderation"
            },"|","|",{
                name: "paste",
                action: paste_prompt_content,
                className: "fa fa-paste",
                title: "Paste Prompt from Clipboard"
            },"|","|",{
                name: "trash",
                action: delete_prompt_content,
                className: "fas fa-trash-alt",
                title: "Delete Prompt"
            },"|","|",{
                name: "copy",
                action: copy_to_clipboard,
                className: "fa-regular fa-copy",
                title: "Copy Prompt to Clipboard"
            }
        ]
    });

    // 文字数カウント領域を作成
    var charCountArea = $('<span>').addClass('char-count');
    charCountArea.text("0");

    // トークンカウント領域を作成
    var tokenCountArea = $('<span>').addClass('token-count');
    tokenCountArea.text("0");

    // エディタのステータスバーに追加
    $(simplemde.gui.statusbar).append(charCountArea);
    $(simplemde.gui.statusbar).append(tokenCountArea);

    var delayInMilliseconds = 1000; // 1 second
    var timeoutId;

    simplemde.codemirror.on('change', function() {
        // clear the existing timeout
        clearTimeout(timeoutId);
        timeoutId = setTimeout(function() {
            // 新しいテキストを取得
            var newText = simplemde.value();

            // サーバにリクエストを送信してトークン数を取得
            $.post(REMOTE_URL + '/token_count', { prompt: newText }, function(tokenCount) {
                // トークンカウント領域に結果を表示
                tokenCountArea.text(tokenCount);
            });

            // 文字数を数えて設定
            charCountArea.text(newText.length);
        }, delayInMilliseconds);
    });
}
