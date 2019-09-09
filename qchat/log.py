import logging

LOG_LEVEL = logging.INFO
FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
logging.basicConfig(format=FORMAT)


class QChatLogger:
    """
    Simple logger module used in the QChat project, overrides the default logger but allows space for any additional
    desired functionalities.
    """
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

    def exception(self, message):
        self.logger.exception(message)
