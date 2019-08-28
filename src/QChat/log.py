import logging

LOG_LEVEL = logging.INFO
FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
logging.basicConfig(format=FORMAT)


class QChatLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVEL)

    def warning(self, message):
        self.logger.warning(message)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def error(self, message):
        self.logger.error(message)