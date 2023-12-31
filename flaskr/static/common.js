$(document).ready(function() {
    $('[data-dismiss="alert"]').on('click', function() {
        $(this).closest('.alert').stop().fadeOut();
    });

    // ハンバーガーメニューをクリックしたときの処理
    $(".hamburger-menu").click(function() {
        // メニューコンテンツの表示・非表示を切り替える
        $(".menu-content").toggle();
    });
});

// function getCurrentDateTime() {
//     var now = new Date();
//     var year = now.getFullYear();
//     var month = ("0" + (now.getMonth() + 1)).slice(-2); // Months are zero indexed, so we add 1
//     var day = ("0" + now.getDate()).slice(-2);
//     var hour = ("0" + now.getHours()).slice(-2);
//     var minute = ("0" + now.getMinutes()).slice(-2);
//     var second = ("0" + now.getSeconds()).slice(-2);
//     var millisecond = ("00" + now.getMilliseconds()).slice(-3); // Milliseconds can be 1-3 digits long
//     return "" + year + month + day + hour + minute + second + millisecond;
// }

function getCurrentDateTime() {
    var now = new Date();
    var year = now.getFullYear();
    var month = String(now.getMonth() + 1).padStart(2, '0');
    var day = String(now.getDate()).padStart(2, '0');
    var hours = String(now.getHours()).padStart(2, '0');
    var minutes = String(now.getMinutes()).padStart(2, '0');
    var seconds = String(now.getSeconds()).padStart(2, '0');
    
    return year + month + day + hours + minutes + seconds;
}

function showSuccessMessage(message, duration) {
    $('.alert-success .alert-message-text').text(message);
    $('.alert-success').fadeIn().delay(duration).fadeOut();
}

function showWarningMessage(message, duration) {
    $('.alert-warning .alert-message-text').text(message);
    $('.alert-warning').fadeIn().delay(duration).fadeOut();
}

function showInfoMessage(message, duration) {
    $('.alert-info .alert-message-text').text(message);
    if (duration >0) {
        $('.alert-info').fadeIn().delay(duration).fadeOut();
    } else {
        $('.alert-info').fadeIn();
    }
}

function makeRandomString(characters, len)
{
	var passwd = "";
	for (var i = 0; i < len; i++) {
		var idx = Math.random() * characters.length;
		passwd += characters.charAt(idx);
	}
	return passwd;
}

// UUID文字列を生成する。
function mkuuid()
{
	var CHARACTERS = "0123456789abcdef";
	var uuid = 
		  makeRandomString(CHARACTERS, 8)
		+ "-"
		+ makeRandomString(CHARACTERS, 4)
		+ "-"
		+ makeRandomString(CHARACTERS, 4)
		+ "-"
		+ makeRandomString(CHARACTERS, 4)
		+ "-"
		+ makeRandomString(CHARACTERS, 12);
	return uuid;
}

function formatNumber(num) {
    if (num < 0.0001) {
        return '0.000';
    } else {
        return num.toFixed(3);
    }
}

function getClipboardContent() {
    // テキストエリアを一時的に作成してクリップボードの内容を取得
    var tempTextArea = $('<textarea>');
    tempTextArea.css({ position: 'absolute', left: '-9999px' }).appendTo('body').focus();
    document.execCommand('paste');
    var clipboardContent = tempTextArea.val();
    tempTextArea.remove();
    return clipboardContent;
}

// ローディングアイコンを表示する関数
function showLoadingIcon() {
    document.getElementById('loadingIcon').style.display = 'block';
}

// ローディングアイコンを非表示にする関数
function hideLoadingIcon() {
    document.getElementById('loadingIcon').style.display = 'none';
}

let translations = {};
let fetchFailed = false;

function get_translation_data() {
    // すでに取得に失敗している場合は再度取得しない
    if (fetchFailed) {
        return;
    }

    let timestamp = new Date().getTime();
    fetch(`/translations.js?${timestamp}`)
        .then(response => {
            if (!response.ok) {
                fetchFailed = true;
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (Object.keys(data).length === 0) {
                fetchFailed = true;
                throw new Error('Empty translation data');
            }
            translations = data;
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error.message);
        });
}

function gettext(message) {
    if (Object.keys(translations).length === 0 && !fetchFailed) {
        get_translation_data();
    }
    var result = translations[message];
    return result ? result : message;
}

function getTextFromDiv($div) {
    // divからhtmlを取得する
    let htmlToCopy = $div.html();

    // <br>タグを一時的なプレースホルダーに置き換える
    htmlToCopy = htmlToCopy.replace(/<br\s*\/?>/gi, 'PLACEHOLDER_FOR_NEWLINE');

    // 一時的な要素を作成し、HTMLをセット
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlToCopy;

    // 一時的な要素からテキストを取得
    let textToCopy = tempDiv.innerText;  // tempDiv.textContent || tempDiv.innerText;

    // プレースホルダーを改行コードに置き換える
    textToCopy = textToCopy.replace(/PLACEHOLDER_FOR_NEWLINE/g, '\n');

    return textToCopy;
}
