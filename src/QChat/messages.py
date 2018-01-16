import json
import threading

HEADER_LENGTH = 4
PAYLOAD_SIZE = 4
MAX_SENDER_LENGTH = 16

class MalformedMessage(Exception):
    pass


class Message:
    header = b'MSSG'
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
            elif type(message_data) == bytes:
                self.data = json.loads(str(message_data, 'utf-8'))
            else:
                raise MalformedMessage
        except:
            raise MalformedMessage

    def encode_message(self):
        padded_sender = (b'\x00'*MAX_SENDER_LENGTH + bytes(self.sender, 'utf-8'))[-16:]
        try:
            byte_data = bytes(json.dumps(self.data), 'utf-8')
        except:
            raise MalformedMessage

        size = len(byte_data).to_bytes(PAYLOAD_SIZE, 'big')
        return self.header + padded_sender + size + byte_data


class RGSTMessage(Message):
    header = b'RGST'


class AUTHMessage(Message):
    header = b'AUTH'


class QCHTMessage(Message):
    header = b'QCHT'


class PUTUMessage(Message):
    header = b'PUTU'


class GETUMessage(Message):
    header = b'GETU'


class BB84Message(Message):
    header = b'BB84'

class PTCLMessage(Message):
    header = b'PTCL'

class CQCCMessage(Message):
    header = b'CQCC'


class MessageFactory:
    def __init__(self):
        self.message_mapping = {
            Message.header: Message,
            RGSTMessage.header: RGSTMessage,
            AUTHMessage.header: AUTHMessage,
            PUTUMessage.header: PUTUMessage,
            GETUMessage.header: GETUMessage,
            QCHTMessage.header: QCHTMessage,
            BB84Message.header: BB84Message,
            PTCLMessage.header: PTCLMessage,
            CQCCMessage.header: CQCCMessage
        }

    def create_message(self, header, sender, message_data):
        return self.message_mapping[header](sender, message_data)
