from collections import namedtuple

# namedtupleでChatGptModelを定義。
# modelName: モデル名
# summarizeTokenLimit: 要約のトークン数制限
# sendTokenLimit: トークン送信の制限数
# 要約をする際、直近のChatから遡り、次のどちらかまでは要約に含めずに残す。
# restChatSize: 要約時、要約対象としない直近のChatの会話数。user/assistantの一方向送信を1で数え、偶数（往復）を指定する。
# restTokens:   要約時、要約対象としない直近のChatのトークン数。
ChatGptModel = namedtuple('ChatGptModel', [
    'modelName',
    'summarizeTokenLimit', 
    'sendTokenLimit',
    'restChatSize',
    'restTokens'
])

# ChatGPT_35_Turbo の設定値
ChatGPT_35_Turbo = ChatGptModel(
    modelName='gpt-3.5-turbo',
    summarizeTokenLimit=3200,
    sendTokenLimit=3300,
    restChatSize=0,
    restTokens=1000
)

# ChatGPT_4 の設定値
ChatGPT_4 = ChatGptModel(
    modelName='gpt-4',
    summarizeTokenLimit=5600,  #7000,
    sendTokenLimit=5600,  #7450,
    restChatSize=0,  #20,
    restTokens=1600
)
