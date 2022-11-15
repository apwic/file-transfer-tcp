import lib.connection as con
from lib.segment import Segment
import lib.segment as segment
import lib.argParser as argParser
import lib.config as config
import socket
import math

class Server:
    def __init__(self):
        # Init server
        parser = argParser.ArgParserServer()
        args = parser.parse()
        
        # connection
        self.ip = config.LOCAL_IP
        self.port = args.port
        self.server = con.Connection(self.ip, self.port)
        self.addrList = []

        # file transer
        self.path = args.path
        with open(self.path, "rb") as f:
            f.seek(0,2)
            self.fileSize = f.tell()

        self.segment = math.ceil(self.fileSize / (config.SEGMENT_SIZE))

        print(f"[!] Server is running on {self.ip}:{self.port}")
        print(f"[!] Waiting for client to connect...")

    def listen_for_clients(self):
        # Waiting client for connect
        while True:
            dataSegment, addr = self.server.listen_single_segment()
            print(f"[!] Received request from {addr[0]}:{addr[1]}")

            # Check for address in list
            if (addr not in self.addrList):
                self.addrList.append(addr)

            userPrompt = input("[?] Listen more? (y/n) ")

            if (userPrompt.lower() == "n"):
                print("\nClient list:")
                for i in range(len(self.addrList)):
                    print(f"[{i + 1}] {self.addrList[i][0]}:{self.addrList[i][1]}")
                print()
                break
            
        # loop tiap client
        # self.three_way_handshake()

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        print(f"[!] Starting three way handshake with clients...")
        for clients in self.addrList:
            if (self.three_way_handshake(clients)):
                print(f"[!] Three way handshake with {clients[0]}:{clients[1]} success")
                print(f"[!] Starting file transfer with {clients[0]}:{clients[1]}")
                self.file_transfer(clients)
            else:
                print(f"[!] Three way handshake with {clients[0]}:{clients[1]} failed")


    def file_transfer(self, client_addr : ("ip", "port")):
        # File transfer, server-side, Send file to 1 client
        # N  := window size
        # Sb := sequence base
        # Sm := sequence max

        # window size might be bigger than file size
        # need to check window bound
        windowBound = min(config.WINDOW_SIZE, self.segment)
        seqBase = 0
        seqMax = config.WINDOW_SIZE

        # send file per segment
        with open(self.path, "rb") as f:
            while seqBase < self.segment:
                # Send segment
                for i in range(seqBase, windowBound):
                    f.seek(i * config.SEGMENT_DATA_SIZE)
                    dataSegment = Segment()
                    dataSegment.set_header({"seqNum": i, "ackNum": 0})
                    dataSegment.set_payload(f.read(config.SEGMENT_DATA_SIZE))
                    self.server.send_data(dataSegment, client_addr)
                    print(f"[Segment SEQ={i}] Sent to {client_addr[0]}:{client_addr[1]}")

                # Listen for ACK
                seqMax = windowBound
                while seqBase < seqMax:
                    try:
                        dataSegment, addr = self.server.listen_single_segment()
                        if (dataSegment.get_flag().ACK and dataSegment.valid_checksum() and addr == client_addr):
                            if (dataSegment.get_header()["ackNum"] == seqBase):
                                seqBase += 1
                                windowBound = min(seqBase + config.WINDOW_SIZE, self.segment)
                            # ackNum > seqBase it means that client already received the segment
                            # but ACK flag is lost
                            elif (dataSegment.get_header()["ackNum"] > seqBase):
                                seqBase = dataSegment.get_header()["ackNum"] + 1
                                windowBound = min(seqBase + config.WINDOW_SIZE, self.segment)
                            print(f"[Segment SEQ={seqBase}] ACK from {addr[0]}:{addr[1]}")
                        else:
                            print(f"[Segment SEQ={seqBase}] Error from {addr[0]}:{addr[1]}")
                    except socket.timeout:
                        print(f"[!] Timeout, resending segment from {seqBase} to {windowBound}")
                        break
        
        # send FIN to client
        dataSegment = Segment()
        dataSegment.set_flag([segment.FIN_FLAG])
        self.server.send_data(dataSegment, client_addr)
        print(f"[!] FIN file transfer sent to {client_addr[0]}:{client_addr[1]}")

        # listen for ACK
        try:
            if (self.server.listen_single_segment()[0].get_flag().ACK):
                print(f"[!] ACK file transfer with {client_addr[0]}:{client_addr[1]} success")
            else:
                print(f"[!] ACK file transfer with {client_addr[0]}:{client_addr[1]} failed")
        except socket.timeout:
            print(f"[!] ACK file transer with {client_addr[0]}:{client_addr[1]} time out")



    def three_way_handshake(self, client_addr) -> bool:
        # Three Way Handshake, server-side as initiator
        print(f"[!] Server initiating three-way handshake to client {client_addr[0]}:{client_addr[1]}")

        # 1. server sends SYN flag to destined client
        req = Segment()
        req.set_flag([segment.SYN_FLAG])
        self.server.send_data(req, (client_addr))

        # 2. server waits for client to send SYN-ACK resp
        dataSegment, addr = self.server.listen_single_segment()
        if (not dataSegment.valid_checksum()):
            print(f"[!] Checksum failed")
            return False

        if (dataSegment.get_flag().SYN and dataSegment.get_flag().ACK):
            # 3. server sends ACK on SYN-ACK resp
            ack = Segment()
            ack.set_flag([segment.ACK_FLAG])
            self.server.send_data(ack, (client_addr))

            print(f"[!] Three-way handshake with client {client_addr[0]}:{client_addr[1]} success")
            return True
        else:
            print(f"[!] Three-way handshake with client {client_addr[0]}:{client_addr[1]} failed")
            print(f"[!] Closing connection")
            return False


if __name__ == '__main__':
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()