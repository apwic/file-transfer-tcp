import lib.connection as con
from lib.segment import Segment, SegmentFlag
import lib.segment as segment

localIp = "127.0.0.1"

class Client:
    def __init__(self, ip, port):
        # Init client
        self.client = con.Connection(ip, port)
        self.three_way_handshake()
        while True:
            message = input("masukkan pesan: ")

            msg = Segment()
            msg.set_flag([segment.ACK_FLAG])
            msg.set_header({'seqNum': 0, 'ackNum': 1})
            msg.set_payload(bytes(message, 'ascii'))
            self.client.send_data(msg, (ip, 1337))
            print("sent")

    def three_way_handshake(self):
        # Three Way Handshake, client-side

        # 1. client sent SYN flag to server
        req = Segment()
        req.set_flag([segment.SYN_FLAG])
        self.client.send_data(req, (self.client.ip, 1337))

        # 2. client wait for server to send SYN-ACK resp
        dataSegment, addr = self.client.listen_single_segment()
        print(dataSegment)
        if (dataSegment.get_flag().SYN and dataSegment.get_flag().ACK):
            # 3. client sends ACK on SYN-ACK resp
            ack = Segment()
            ack.set_flag([segment.ACK_FLAG])
            self.client.send_data(ack, (self.client.ip, 1337))

    def listen_file_transfer(self):
        # File transfer, client-side
        pass


if __name__ == '__main__':
    main = Client(localIp, 3006)
    # main.three_way_handshake()
    # main.listen_file_transfer()
