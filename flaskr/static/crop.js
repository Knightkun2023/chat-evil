$(document).ready(function() {
    function readImage(file) {
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                // img要素にData URLを設定
                var image = new Image();
                image.src = e.target.result;

                let imageArea = document.getElementById('image_area');
                imageArea.innerHTML = '';
                imageArea.classList.add('hide');
                imageArea.appendChild(image);

                image.onload = function() {
                    // Cropper.jsを初期化
                    window.my_cropper = new Cropper(image, {
                        // ここでオプションを設定できる
                        aspectRatio: 1
                    });
                    imageArea.classList.remove('hide');
 
                    document.getElementById('rotationSlider').addEventListener('input', function() {
                        var angle = this.value;
                        window.my_cropper.rotateTo(angle); // スライダーの値に応じて画像を回転
                    });
                };
            };
            reader.readAsDataURL(file);
        }
    }

    function setupInitialImageArea() {
        var imageArea = document.getElementById('image_area');
        imageArea.innerHTML = ''; // imageAreaを空にする
    
        var spanElement = document.createElement('span');
        spanElement.id = 'load_image_message';
        spanElement.innerHTML = 'クリックするかドラッグ＆ドロップで<br>画像を読み込む。';
        var loadingArea = document.createElement('div');
        loadingArea.id = 'loading_area';
        loadingArea.appendChild(spanElement);
        imageArea.appendChild(loadingArea);

        // ファイルを読み込むダイアログを表示する。
        $('#loading_area').click(function() {
            $('#load_image').click();
        });

        $("#loading_area").on("dragover", function(event) {
            event.preventDefault();  
            event.stopPropagation();
            $(this).css('border', '2px solid #0B85A1');
        });
    
        $("#loading_area").on("dragleave", function(event) {
            event.preventDefault();  
            event.stopPropagation();
            $(this).css('border', '2px dashed #ccc');
        });
    
        $("#loading_area").on("drop", function(event) {
            event.preventDefault();  
            event.stopPropagation();
            $(this).css('border', '2px dashed #ccc');
            var files = event.originalEvent.dataTransfer.files;
            readImage(files[0]);
        });
    }

    // 初期設定
    setupInitialImageArea();
    
    // キャンセルボタンのイベントハンドラ
    $('#cancel_button').click(function() {
        // Cropperのインスタンスが存在する場合、破棄する
        if (window.my_cropper) {
            window.my_cropper.destroy();
            window.my_cropper = null;
        }

        // プレビューが表示されていれば削除する。
        let preview = document.getElementById('preview');
        // previewにセットする
        preview.src = "";
        $('#image_data').val('');

        // 初期状態に戻す
        setupInitialImageArea();
    });
 
    $('#load_image').change(function() {
        var file = this.files[0];
        readImage(file);
    });

    // function readImage(file) {
    //     var imageArea = document.getElementById('image_area');
    //     imageArea.innerHTML = ''; // imageAreaを空にする
    //     var reader = new FileReader();
    //     reader.onload = function(e) {
    //         $("#image_area").attr('src', e.target.result);
    //         $("#image_area").show();
    //     }
    //     reader.readAsDataURL(file);
    // }

    let cropButton = document.getElementById('crop_button');
    cropButton.addEventListener('click', function () {
        // トリミングパネル内のcanvasを取得
        let canvas = window.my_cropper.getCroppedCanvas({
            width: 384,
            height: 384
        });
        // canvasをbase64に変換
        let data = canvas.toDataURL();
        
        let preview = document.getElementById('preview');
        // previewにセットする
        preview.src = data;
        $('#image_data').val(data);
    });
});
