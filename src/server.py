import lib.connection as con
from lib.segment import Segment
import lib.segment as segment

localIp = "127.0.0.1"

class Server:
    def __init__(self, ip, port):
        # Init server
        self.server = con.Connection(ip, port)
        print("server up and listening")

    def listen_for_clients(self):
        # Waiting client for connect
        self.three_way_handshake()
        while True:
            dataSegment, addr = self.server.listen_single_segment()
            print(dataSegment)
            print("client ip addr: ", addr)

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass

    def file_transfer(self, client_addr : ("ip", "port")):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self) -> bool:
        # Three way handshake, server-side, 1 client
        # 1. server get SYN flag from client
        dataSegment, addr = self.server.listen_single_segment()
        print(dataSegment)
        if (dataSegment.get_flag().SYN):
            # 2. server sent SYN-ACK flag to client
            synAck = Segment()
            synAck.set_flag([segment.SYN_FLAG, segment.ACK_FLAG])
            self.server.send_data(synAck, addr)
            # 3. server get ACK flag from client
            dataSegment, addr = self.server.listen_single_segment()
            if (dataSegment.get_flag().ACK):
                print(dataSegment)
                print("ANJAY ACEKA")
                return True
            else:
                print("LOH GA ACEKA ???")

        return False


if __name__ == '__main__':
    main = Server(localIp, 1337)
    main.listen_for_clients()
    # if (main.three_way_handshake()):
    #     print("anjay ngab")
    # main.start_file_transfer()
