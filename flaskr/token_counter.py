from flask import request
from . import app
from .utils.commons import count_token

@app.route('/token_count', methods=['POST'])
#@login_required
def token_counter():
    prompt = request.form.get('prompt')
    return str(count_token(prompt))   # トークン数を返す。
