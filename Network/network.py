import socket
import json, pickle
from time import time


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class Network:

    def __init__(self, user_id: str):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # self.host = socket.gethostbyname(socket.gethostname())
        self.host = get_ip()
        self.port = 5555

        self.id = 0
        self.user_id = user_id
        print("Id: ", self.id, self.user_id)

        self.addr = (self.host, self.port)
        self.on_connect_data = json.loads(self.connect())

        self.messages = []
        self.sendTime = time()

    def connect(self):
        self.client.connect(self.addr)
        self.client.send(self.user_id.encode())
        return self.client.recv(30000).decode()

    def disconnect(self):
        self.client.close()

    def send(self, data):
        self.sendTime = time()
        """
        :param player_data:
        :param data: str
        :return: str
        """
        try:
            self.client.send(str.encode(data))
            reply = self.client.recv(10000).decode()

            return reply, time() - self.sendTime
        except socket.error as e:
            return str(e)
