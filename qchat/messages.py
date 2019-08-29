import json

HEADER_LENGTH = 4
PAYLOAD_SIZE = 4
MAX_SENDER_LENGTH = 16


class MalformedMessage(Exception):
    pass


class Message:
    header = b'MSSG'
    verify = False
    strip = False
    def __init__(self, sender, message_data):
        """
        Initializes application specific message structure for use with QChat
        :param sender: Host sending the message
        :param message_data: Dictionary containing the message data to retain
        """
        if len(sender) > MAX_SENDER_LENGTH:
            raise MalformedMessage("Length of sender too long")
        self.sender = sender
        self.unpack_message_data(message_data)

    def unpack_message_data(self, message_data):
        """
        Transforms the message data into JSON serializable format which can be encoded/decoded
        into a byte string for communication through the sockets library
        :param message_data:
        :return:
        """
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
        """
        Encodes the messages information into a byte string that can be unpacked into a Message
        object on the recieving application's end
        :return: Byte string encoding the message object's information
        """
        padded_sender = (b'\x00'*MAX_SENDER_LENGTH + bytes(self.sender, 'utf-8'))[-16:]
        try:
            byte_data = bytes(json.dumps(self.data), 'utf-8')
        except:
            raise MalformedMessage

        size = len(byte_data).to_bytes(PAYLOAD_SIZE, 'big')
        return self.header + padded_sender + size + byte_data


class RGSTMessage(Message):
    """
    Registration message used for registering new users to the host's user database
    """
    header = b'RGST'


class AUTHMessage(Message):
    header = b'AUTH'


class QCHTMessage(Message):
    """
    QChat message used for the primary chat's client interface
    """
    header = b'QCHT'
    verify = True
    strip = True


class GETUMessage(Message):
    """
    GET User message sent to hosts when requesting user information from other
    known hosts in the application network
    """
    header = b'GETU'
    strip = True


class PUTUMessage(Message):
    """
    PUT User message response to GET User when requesting user information from
    other known hosts in the application network
    """
    header = b'PUTU'
    strip = True


class PTCLMessage(Message):
    """
    Protocol initialization message that instructs the recieving host to assume the
    follower's role in the requested protocol
    """
    header = b'PTCL'
    verify = True
    strip = True


class RQQBMessage(Message):
    """
    ReQuest QuBit message that instructs a server to act as an EPR source between to applications
    in the network
    """
    header = b'RQQB'


class BB84Message(Message):
    """
    BB84 QKD Protocol control messages used for coordinating BB84 protocol specific
    classical messages between executing protocols
    """
    header = b'BB84'
    verify = True
    strip = True


class DQKDMessage(Message):
    """
    DIQKD Protocol control messages used for coordinating DIQKD protocol specific
    classical messages between executing protocols
    """
    header = b'DQKD'
    verify = True
    strip = True


class SPDSMessage(Message):
    """
    SuPerDenSe protocol control message used for coordinating SuperDense Coding protocol
    specific classical messages between executing protocols
    """
    header = b'SPDS'
    verify = True
    strip = True


class MessageFactory:
    def __init__(self):
        """
        Initializes a message factory that is used by QChat connection for converting the byte
        string encoded message into the appropriate message object for use by the server application
        """
        self.message_mapping = {
            Message.header: Message,
            RGSTMessage.header: RGSTMessage,
            AUTHMessage.header: AUTHMessage,
            PUTUMessage.header: PUTUMessage,
            GETUMessage.header: GETUMessage,
            QCHTMessage.header: QCHTMessage,
            BB84Message.header: BB84Message,
            PTCLMessage.header: PTCLMessage,
            RQQBMessage.header: RQQBMessage,
            SPDSMessage.header: SPDSMessage,
            DQKDMessage.header: DQKDMessage
        }

    def create_message(self, header, sender, message_data):
        return self.message_mapping[header](sender, message_data)
