import os, requests, re
from .commons import create_error_info

# モデレーションのカテゴリのキー。この順序で格納する。
moderation_category_keys = [
    "harassment",
    "harassment/threatening",
    "hate",
    "hate/threatening",
    "self-harm",
    "self-harm/instructions",
    "self-harm/intent",
    "sexual",
    "sexual/minors",
    "violence",
    "violence/graphic"
]

# モデレーションのflaggedの圧縮に使用するBase64エンコードの文字。この順番に使用する。
moderation_base64_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/"

def encode_base64_str(binary_str):

    # 11ビットを12ビットにする
    binary_str += "0"
    # 文字列を6ビットずつ2つに分割
    first_6bit = binary_str[:6]
    second_6bit = binary_str[6:]

    # 6ビットを整数に変換
    first_int = int(first_6bit, 2)
    second_int = int(second_6bit, 2)

    # Base64文字に変換
    encoded_str = moderation_base64_chars[first_int] + moderation_base64_chars[second_int]

    return encoded_str

def decode_base64_str(encoded_str):

    # 2文字のBase64文字をそれぞれの6ビットの整数に変換
    first_int = moderation_base64_chars.index(encoded_str[0])
    second_int = moderation_base64_chars.index(encoded_str[1])

    # 整数を6ビットの文字列に変換
    first_6bit = format(first_int, '06b')
    second_6bit = format(second_int, '06b')

    # 2つの6ビットの文字列を結合して、末尾のビットを取り除いて11ビットにする
    binary_str = first_6bit + second_6bit[:-1]

    return binary_str

def get_binary_flagged(data):
    flagged = ''
    if data['results'][0]['flagged']:
        for key in moderation_category_keys:
            # print(key)
            if data['results'][0]['categories'][key]:
                flagged = flagged + '1'
            else:
                flagged = flagged + '0'
        flagged = encode_base64_str(flagged)
    return flagged

def round_to_3rd_decimal(float_num):
    # 小数点第四位で四捨五入
    rounded_num = round(float_num, 3)
    return f"{rounded_num:.3f}"

def convert_decimal_str_to(dec_str):
    if dec_str[0] == '1':
        return '1*'
    if dec_str[2:5] == '000':
        return '0*'
    return dec_str[2:5]

def code_score(float_num):
    return convert_decimal_str_to(round_to_3rd_decimal(float_num))

def code_scores(data):
    coded_scores = ''
    for key in moderation_category_keys:
        # print(key)
        score = data['results'][0]['category_scores'][key]
        coded_scores = coded_scores + code_score(score)

    return coded_scores if coded_scores != '0*0*0*0*0*0*0*0*0*0*0*' else ''

def decode_score(coded_scores) -> list:
    index = 0
    result_list = []

    if coded_scores == '':
        coded_scores = '0*0*0*0*0*0*0*0*0*0*0*'

    while len(coded_scores) > index:
        if coded_scores[index + 1] == '*':
            if coded_scores[index] == '1':
                result_list.append(1.000)
            else:
                result_list.append(0.000)
            index = index + 2
        else:
            score = float('0.' + coded_scores[index:index + 3])
            result_list.append(score)
            index = index + 3

    return result_list

def code_moderation_json(data: dict) -> str:
    coded_data = []
    coded_data.append(data['id'])
    coded_data.append(data['model'])

    coded_flagged = get_binary_flagged(data)
    coded_data.append(coded_flagged)

    coded_scores = code_scores(data)
    coded_data.append(coded_scores)
    
    return ','.join(coded_data)

def decode_moderation_str(coded_str: str) -> dict:
    coded_data = coded_str.split(',')
    result_dict = {}
    result_dict['id'] = coded_data[0]
    result_dict['model'] = coded_data[1]

    result = {}
    if coded_data[2] == '':
        result['flagged'] = False
        result['categories'] = {}
        for key in moderation_category_keys:
            result['categories'][key] = False
    else:
        result['flagged'] = True
        binary_flagged = decode_base64_str(coded_data[2])
        result['categories'] = {}
        index = 0
        for key in moderation_category_keys:
            result['categories'][key] = binary_flagged[index] == '1'
            index = index + 1

    result['category_scores'] = {}
    score_list = decode_score(coded_data[3])
    index = 0
    for key in moderation_category_keys:
        result['category_scores'][key] = score_list[index]
        index = index + 1

    result_dict['results'] = []
    result_dict['results'].append(result)

    return result_dict

def get_moderation_result(content, key, moderation_model_no=1) -> dict:
    moderation_model = 'text-moderation-latest'
    if moderation_model_no == 2:
        moderation_model = 'text-moderation-stable'
    
    url = "https://api.openai.com/v1/moderations"
    headers = {
        "Authorization": "Bearer " + key,
    }
    payload = {
        "input": content,
        "model": moderation_model
    }

    response = requests.post(url, headers=headers, json=payload)
    print("@@@@@@@@@@ moderation response: " + str(response.json()))

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {"error": {
            "status_code": response.status_code,
            "text": response.text
        }}

def get_moderation_result_simply(content, key, moderation_model_no=1) -> dict:
    result_dict = get_moderation_result(content, key, moderation_model_no)
    if 'error' in result_dict:
        error_info = create_error_info(message='Error ocurred in Moderation API.', status=500, path='get_moderation_result_simply')
        error_info['results'] = []
        return error_info

    result_val = 'ok'
    if 'results' in result_dict and len(result_dict['results']) > 0:
        result_elem = result_dict['results'][0]
        if 'category_scores' in result_elem:
            category_scores = result_elem['category_scores']
            if 'sexual' in category_scores and category_scores['sexual'] > 0.270:
                result_val = 'orange'
            if 'sexual/minors' in category_scores and category_scores['sexual/minors'] > 0.200:
                result_val = 'red'
        if result_val == 'ok' and 'flagged' in result_elem and result_elem['flagged']:
            result_val = 'orange'
    
    return {'result_val': result_val, 'result_dict': result_dict}

def check_moderation_main(content, moderation_model_no):
    result_dict = get_moderation_result_simply(content=content, key=os.environ['OPENAI_API_KEY'], moderation_model_no=moderation_model_no)

    response_code = 200
    if 'error' in result_dict:
        # エラーだった場合
        response_code = 400
        dic = {'error': result_dict['error'], 'error_message':'Error'}
        result_dict = dic

    return result_dict, response_code

def check_sorry_message(text) -> bool:
    result = False
    for ng_text in ('申し訳', "I'm sorry, but", 'OpenAI.*(ポリシー|規約)', 'OpenAI.*(policy|policies|does not)', 'コンテンツには応じることができません', '本システムは.*対応しておりません'):
        if re.search(ng_text, text, flags=re.IGNORECASE):
            result = True
            break

    return result
