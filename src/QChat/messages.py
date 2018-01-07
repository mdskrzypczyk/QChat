import json

PAYLOAD_SIZE = 4
MAX_SENDER_LENGTH = 16

class MalformedMessage(Exception):
    pass


class Message:
    header = b'MSSG'
    def __init__(self, sender, message_data):
        if len(sender) > MAX_SENDER_LENGTH:
            raise Exception("Length of sender too long")
        self.sender = sender
        self.unpack_message_data(message_data)

    def unpack_message_data(self, message_data):
        try:
            self.data = json.loads(str(message_data))
        except:
            raise MalformedMessage


    def encode_message(self):
        padded_sender = (b'\x00'*MAX_SENDER_LENGTH + self.sender)[-16:]
        try:
            byte_data = bytes(json.dumps(self.data))
        except:
            raise MalformedMessage

        size = len(self.data).to_bytes(SIZE_LENGTH, 'big')
        return self.header + padded_sender + size + byte_data


class RGSTMessage(Message):
    header = b'RGST'


class AUTHMessage(Message):
    header = b'AUTH'


class QCHTMessage(Message):
    header = b'QCHT'
