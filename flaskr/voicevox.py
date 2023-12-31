### Code by https://qiita.com/hatt_takumi (匠 服部)
### https://qiita.com/hatt_takumi/items/d65c243294f250724c19
########################################################################
import json
import requests
import wave

def generate_wav(text, speaker=1, filepath='./audio.wav', protocol='http', host='localhost', port=50021):

    try:
        params = (
            ('text', text),
            ('speaker', speaker),
        )
        remote_url = protocol + '://' + host + ':' + str(port)
        response1 = requests.post(
            f'{remote_url}/audio_query',
            params=params
        )
        response1.raise_for_status()  # ステータスコードが200系でなければ例外を投げる

        headers = {'Content-Type': 'application/json',}
        response2 = requests.post(
            f'{remote_url}/synthesis',
            headers=headers,
            params=params,
            data=json.dumps(response1.json())
        )
        response2.raise_for_status()  # ステータスコードが200系でなければ例外を投げる

        wf = wave.open(filepath, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(response2.content)
        wf.close()
    except:
        pass

def get_speakers(protocol='http', host='localhost', port=50021) -> list:
    remote_url = protocol + '://' + host + ':' + str(port)
    headers = {'Content-Type': 'application/json',}
    try:
        response = requests.get(
            f'{remote_url}/speakers',
            headers
        )
        response.raise_for_status()  # ステータスコードが200系でなければ例外を投げる
        return response.json()
    except:
        return []

if __name__ == '__main__':
    text = 'こんにちは！'
#    generate_wav(text)
    get_speakers()
