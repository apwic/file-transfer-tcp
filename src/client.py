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

        #initiate client connection to server
        self.client.send_data(Segment(), (self.ip, self.dest_port))
        print(f"[!] Client is running on {self.ip}:{self.port}")


    def three_way_handshake(self):
        # Three way handshake, client-side
        # 1. clent gets SYN flag from server
        try:
            dataSegment, addr = self.client.listen_single_segment()
            self.client.set_timeout(config.ACK_TIMEOUT)
            if (dataSegment.get_flag().SYN and dataSegment.valid_checksum()):
                # 2. client sends SYN-ACK flag to server
                synAck = Segment()
                synAck.set_flag([segment.SYN_FLAG, segment.ACK_FLAG])
                self.client.send_data(synAck, addr)
                # 3. client gets ACK flag from server
                dataSegment, addr = self.client.listen_single_segment()
                if (dataSegment.get_flag().ACK and dataSegment.valid_checksum()):
                    print(f"[!] Three-way handshake with server {addr[0]}:{addr[1]} success")
                else:
                    print(f"[!] Three-way handshake with server {addr[0]}:{addr[1]} ACK Flag not received")
                    print(f"ACK: {dataSegment.get_flag().ACK} AND Checksum: {dataSegment.valid_checksum()}")
            else:
                print(f"[!] Three-way handshake with server {addr[0]}:{addr[1]} failed")
                exit(1)
        except socket.timeout:
            print(f"[!] Three-way handshake with server timed out")
            exit(1)

    def listen_file_transfer(self):
        # File transfer, client-side
        self.client.set_timeout(config.LISTEN_TRANSFER_TIMEOUT)
        fin  = False
        reqNum = 0
        with open(self.path, "wb") as f:
            while(not(fin)):
                try:
                    dataSegment, addr = self.client.listen_single_segment()
                    if (dataSegment.valid_checksum()):
                        seqNum = dataSegment.get_header()["seqNum"]
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
