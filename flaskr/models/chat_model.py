

class ChatModel:
    def __init__(self, modelName):
        self.__modelName = modelName
        self.__history = []
        pass

    def _get_modelName(self):
        return self.__modelName

    def _get_history(self):
        return self.__history

    def addMessage(self, role, content):
        self.__history.append(self._getDict(role=role, content=content))

    def getNextMessage(self, content):
        pass

    def _getDict(self, role, content):
        pass

    @classmethod
    def createInstance(cls, modelName):
        if modelName.startswith('gpt-'):
            return ChatGptModel(modelName=modelName)
        elif modelName.startswith('gemini-'):
            return GeminiModel(modelName=modelName)
        else:
            raise ValueError(f'モデル名が不適切で、ChatModel系インスタンスを生成できませんでした。modelName=[{modelName}]')

from openai import OpenAI
from datetime import datetime
from ..utils.commons import get_model_id
class ChatGptModel(ChatModel):
    def __init__(self, modelName):
        super().__init__(modelName=modelName)
    
    def _getDict(self, role, content):
        return {'role': role, 'content': content}

    def getNextMessage(self, content):
        # historyの末尾にcontentを追加
        messages = self._get_history().copy()
        messages.append(self._getDict('user', content))

        client = OpenAI()
        response = client.chat.completions.create(
            model = self._get_modelName(),
            messages = messages
        )

        # アシスタントメッセージと、そのためのトータルのトークン数を取得する
        res = {}
        assistant_message_text = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
        response_id = response.id
        response_created = datetime.fromtimestamp(response.created).strftime('%Y%m%d%H%M%S%f')[:-3]
        response_model = response.model
        response_chatgpt_id = get_model_id(response_model)

        res['assistant_message_text'] = assistant_message_text
        res['total_tokens'] = total_tokens
        res['response_id'] = response_id
        res['response_created'] = response_created
        res['response_model'] = response_model
        res['response_chatgpt_id'] = response_chatgpt_id

        return res

import google.generativeai as genai
import os
from ..utils.commons import get_current_time
class GeminiModel(ChatModel):
    def __init__(self, modelName):
        super().__init__(modelName=modelName)
        genai.configure(api_key=os.environ['GOOGLE_AI_API_KEY'])

        self.__initialized = False
        self.__chat = None
        self._pre_message = ''  # チャットを送る直前の、既存のuserメッセージ。最初のシステムプロンプトなど。

    SAFETY_CONFIGS = [
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",  # BLOCK_ONLY_HIGH , BLOCK_NONE
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",  # BLOCK_ONLY_HIGH , BLOCK_NONE
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",  # BLOCK_ONLY_HIGH , BLOCK_NONE
        },
    ]

    def addMessage(self, role, content):
        current = self._getDict(role=role, content=content)
        history = self._get_history()

        if len(history) == 0:
            if current['role'] != 'user':
                raise ValueError(f"先頭のメッセージのroleは'user'でなければいけません。role={current['role']}")
            history.append(current)
            return
        else:
            if history[-1]['role'] != role:
                history.append(current)
            else:
                combined = history[-1]['parts'] + "\n" + "\n" + content
                history[-1]['parts'] = combined

    def _getDict(self, role, content):
        r = role
        if r == 'assistant':
            r = 'model'
        elif r == 'system':
            r = 'user'
        elif r != 'user':
            raise ValueError(f"roleの値が不適切です。role=[{role}]")
        return {'role': r, 'parts': content}

    def __init_model(self):
        self._pre_message = ''
        hist = self._get_history()
        if len(hist) > 0:
            if hist[0]['role'] != 'user':
                raise ValueError(f"historyの先頭の要素のroleが'user'ではありません。")
            if len(hist) % 2 == 0: # and hist[0]['role'] == 'user' and hist[1]['role'] == 'user':
                if hist[-1]['role'] == 'user':
                    raise ValueError(f"既存のチャット履歴の末尾が'user'ロールで終わっている。parts=[{hist[-1]['parts']}]")
                else:
                    # 問題ない
                    pass
            else:  # 奇数の場合
                if hist[-1]['role'] == 'user':
                    # 既存のチャットがuserで終わっている -> 末尾のチャットを削除、その内容を送信するユーザーメッセージの前につける。
                    last_hist = hist.pop()
                    self._pre_message = last_hist['parts'] + "\n" + "\n"

        model = genai.GenerativeModel(self._get_modelName())
        self.__chat = model.start_chat(history=self._get_history())
        self.__initialized = True

    def getNextMessage(self, content):
        if not self.__initialized:
            self.__init_model()

        new_content = self._pre_message + content
        self._pre_message = ''
        response = self.__chat.send_message(new_content, safety_settings=GeminiModel.SAFETY_CONFIGS)

        # チャットのエラーを取得
        blockedPromptExceptionOccured = False
        block_reason = None
        if response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason
            blockedPromptExceptionOccured = True
        finish_reason = response.candidates[0].finish_reason
        stopCandidateExceptionOccured = False
        if response.candidates[0].finish_reason >= 3:
            stopCandidateExceptionOccured = True

        # アシスタントメッセージと、そのためのトータルのトークン数を取得する
        res = {}
        assistant_message_text = self.__chat.history[-1].parts[0].text
        total_tokens = 0
        response_id = ''
        response_created = get_current_time()
        response_model = self._get_modelName()
        response_chatgpt_id = get_model_id(response_model)

        res['assistant_message_text'] = assistant_message_text
        res['total_tokens'] = total_tokens
        res['response_id'] = response_id
        res['response_created'] = response_created
        res['response_model'] = response_model
        res['response_chatgpt_id'] = response_chatgpt_id

        gemini_res = {}
        gemini_res['blockedPromptExceptionOccured'] = blockedPromptExceptionOccured
        gemini_res['block_reason'] = block_reason
        gemini_res['finish_reason'] = finish_reason
        gemini_res['stopCandidateExceptionOccured'] = stopCandidateExceptionOccured
        gemini_res['candidates'] = response.candidates
        res['gemini_response'] = gemini_res

        return res

