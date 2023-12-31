from flask import render_template, url_for, redirect, request, jsonify
from . import app
from .utils.commons import get_current_time
from flask_login import login_required
import base64, os

@app.route('/test/crop', methods=['GET'])
@login_required
def test_crop():

    image_folder = os.path.join(app.root_path, 'static/faces')
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))])
    image_urls = [url_for('static', filename=f'faces/{f}') for f in image_files]

    # return jsonify(image_urls)
    return render_template(
        'croptest.html', image_urls=image_urls
    ), 200

@app.route('/test/crop', methods=['POST'])
@login_required
def test_crop_save():

    image_data = request.form['image_data']

    # "data:image/jpeg;base64,"の部分を取り除く
    format, imgstr = image_data.split(';base64,')
    decoded_img = base64.b64decode(imgstr)

    # 拡張子を決定
    ext = format.split('/')[-1]  # これで 'jpeg' などの形式を取得できる
    if ext == 'jpeg':
        ext = 'jpg'

    # 保存先のパスを生成
    save_path = os.path.join(app.root_path, f'static/faces/{get_current_time()}.{ext}')

    with open(save_path, 'wb') as f:
        f.write(decoded_img)

    return redirect(url_for('test_crop'))

@app.route('/test/camera/', methods=['GET'])
def test_camera_index():

    image_folder = os.path.join(app.root_path, 'static/faces')
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))])
    image_urls = [url_for('static', filename=f'faces/{f}') for f in image_files]

    return render_template(
        'cameratest.html', image_urls=image_urls
    )

@app.route('/test/camera/upload', methods=['POST'])
def test_camera_upload():
    image = request.files['image']

    # 保存先のパスを生成
    ext = 'jpg'
    save_path = os.path.join(app.root_path, f'static/faces/{get_current_time()}.{ext}')

    if image:
        # image.save(os.path.join('uploads', image.filename))
        image.save(save_path)
        return jsonify({'message': 'Image uploaded successfully!'})
    else:
        return jsonify({'error': 'No image uploaded'}), 400

