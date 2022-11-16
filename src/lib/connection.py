import socket
from .segment import Segment

class Connection:
    def __init__(self, ip : str, port : int):
        # Init UDP socket
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        # self.sock.settimeout(30) # wip: change to constant

    def send_data(self, msg : Segment, dest):
        # Send single segment into destination
        self.sock.sendto(msg.get_bytes(), dest)

    def listen_single_segment(self):
        # Listen single UDP datagram within timeout and convert into segment
        data, addr = self.sock.recvfrom(32768) # wip: change to constant
        dataSegment = Segment()
        dataSegment.set_from_bytes(data)
        return dataSegment, addr

    def close_socket(self):
        # Release UDP socket
        self.sock.close()

    def set_timeout(self, timeout):
        self.sock.settimeout(timeout)
