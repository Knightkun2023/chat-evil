import logging, logging.config, traceback, os, json
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # ソースコードのパスを変換
        record.pathname = record.pathname.replace(os.path.expanduser('~'), '~')
        # 必要に応じてrecord.linenoも変更できる
        # record.lineno = ...

        # メッセージのフォーマットを続行
        formatted_message = super(CustomFormatter, self).format(record)
        
        # 例外がある場合は、そのスタックトレースをフォーマット
        if record.exc_info:
            formatted_message += "\n" + self.formatException(record.exc_info)
        
        return formatted_message

    def formatException(self, exc_info):
        # 例外スタックトレースのパスを置換
        original_traceback = traceback.format_exception(*exc_info)
        modified_traceback = [line.replace(os.path.expanduser('~'), '~') for line in original_traceback]
        return ''.join(modified_traceback)

def configure_logging(app):

    # logging.json
    logging_json_path = Path(__file__).parent / ('logging_' + os.environ['FLASK_ENV'] + '.json')

    # JSON設定の読み込み
    with open(logging_json_path, 'r') as config_file:
        config = json.load(config_file)

    logging.config.dictConfig(config)

    # フォーマッター
    log_format = '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s'
    formatter = CustomFormatter(log_format)

    # 特定のハンドラにカスタムフォーマッタを設定
    logger = logging.getLogger('app_logger')
    for handler in logger.handlers:
        handler.setFormatter(formatter)
