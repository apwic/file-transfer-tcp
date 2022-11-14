import lib.connection as con
from lib.segment import Segment, SegmentFlag
import lib.segment as segment
import lib.argParser as argParser
import lib.config as config
import socket

class Client:
    def __init__(self):
        # Init client
        parser = argParser.ArgParserClient()
        args = parser.parse()

        # file transfer
        self.path = args.path

        self.ip = config.LOCAL_IP
        self.port = args.port
        self.dest_port = args.dest
        self.client = con.Connection(self.ip, self.port)

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        print(f"[!] Client started on {self.ip}:{self.port}")
        print(f"[!] Initiating three-way handshake to {self.ip}:{self.dest_port}")

        # 1. client sent SYN flag to server
        req = Segment()
        req.set_flag([segment.SYN_FLAG])
        self.client.send_data(req, (self.ip, self.dest_port))

        # 2. client wait for server to send SYN-ACK resp
        dataSegment, addr = self.client.listen_single_segment()
        print(dataSegment)
        if (not dataSegment.valid_checksum()):
            print(f"[!] Checksum failed")
            exit(1)

        if (dataSegment.get_flag().SYN and dataSegment.get_flag().ACK):
            # 3. client sends ACK on SYN-ACK resp
            ack = Segment()
            ack.set_flag([segment.ACK_FLAG])
            self.client.send_data(ack, (self.ip, self.dest_port))

            print(f"[!] Three-way handshake with {self.ip}:{self.dest_port} success")
        else:
            print(f"[!] Three-way handshake with {self.ip}:{self.dest_port} failed")
            print(f"[!] Closing connection")
            exit(1)

    def listen_file_transfer(self):
        # File transfer, client-side
        fin  = False
        reqNum = 0
        with open(self.path, "wb") as f:
            while(not(fin)):
                try:
                    dataSegment, addr = self.client.listen_single_segment()
                    if (dataSegment.valid_checksum()):
                        seqNum = dataSegment.get_header["seqNum"]
                        if (seqNum == reqNum):
                            ackResp = Segment()
                            ackResp.set_flag([segment.ACK_FLAG])
                            ackResp.set_header({'seqNum': 0, 'ackNum': reqNum})
                            self.client.send_data(ackResp, (self.ip, self.dest_port))
                            print(f"[Segment SEQ={seqNum}] Received, Ack sent")
                            f.write(dataSegment.get_payload())
                            reqNum += 1
                        elif (dataSegment.get_flag().FIN):
                            fin = True
                            ackResp = Segment()
                            ackResp.set_flag([segment.ACK_FLAG])
                            self.client.send_data(ackResp, (self.ip, self.dest_port))
                            print(f"[!] File transfer completed, sending FIN")
                    else:
                        print(f"[Segment SEQ={seqNum}] Checksum failed. Ack prev sequence number")

                except socket.timeout:
                    print(f"[!] Client timeout, resending ACK for SEQ={reqNum-1}")
                    ackResp = Segment()
                    ackResp.set_flag([segment.ACK_FLAG])
                    ackResp.set_header({'seqNum': 0, 'ackNum': reqNum-1})
                    self.client.send_data(ackResp, (self.ip, self.dest_port))

        # close connection
        print(f"[!] Closing connection")
        self.client.close_socket()


if __name__ == '__main__':
    main = Client()
    main.three_way_handshake()
    main.listen_file_transfer()
