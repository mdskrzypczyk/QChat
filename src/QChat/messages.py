class Message:
    def __init__(self, header, data):
        self.header = header
        self.data = data

    def format_message(self):
        m = b''
        m += self.header + b'\n'
        m += b'SIZE: ' + bytes("{}".format(len(self.data))) + b'\n'
        m += self.data
        return m


class AuthMessage(Message):
    def __init__(self, data):


