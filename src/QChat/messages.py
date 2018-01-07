import json

HEADER_LENGTH = 4
PAYLOAD_SIZE = 4
MAX_SENDER_LENGTH = 16

class MalformedMessage(Exception):
    pass


class Message:
    header = 'MSSG'
    def __init__(self, sender, message_data):
        if len(sender) > MAX_SENDER_LENGTH:
            raise MalformedMessage("Length of sender too long")
        self.sender = sender
        self.unpack_message_data(message_data)

    def unpack_message_data(self, message_data):
        try:
            if type(message_data) == dict:
                self.data = message_data
            elif type(message_data) == str:
                self.data = json.loads(message_data)
            else:
                raise MalformedMessage
        except:
            raise MalformedMessage


    def encode_message(self):
        padded_sender = ('\x00'*MAX_SENDER_LENGTH + self.sender)[-16:]
        try:
            byte_data = json.dumps(self.data)
        except:
            raise MalformedMessage

        size = str(len(byte_data).to_bytes(PAYLOAD_SIZE, 'big'), 'utf-8')
        return self.header + padded_sender + size + byte_data


class RGSTMessage(Message):
    header = 'RGST'


class AUTHMessage(Message):
    header = 'AUTH'


class QCHTMessage(Message):
    header = 'QCHT'


class MessageFactory:
    def __init__(self):
        self.message_mapping = {
            Message.header: Message,
            RGSTMessage.header: RGSTMessage,
            AUTHMessage.header: AUTHMessage,
            QCHTMessage.header: QCHTMessage
        }

    def create_message(self, header, sender, message_data):
        return self.message_mapping[header](sender, message_data)
