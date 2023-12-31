import logging, traceback, os
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

    # ロガーを作成
    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.DEBUG)

    log_format = '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    # フォーマッター
    formatter = CustomFormatter(log_format)

    # 日単位のローテーション
    log_file = 'logs/app.log'
    file_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=30)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 標準出力へのロガー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
