import logging

logger_format = '%(asctime)-15s %(levelname)s %(message)s'

class QChatLogger(logging.getLoggerClass()):
    pass