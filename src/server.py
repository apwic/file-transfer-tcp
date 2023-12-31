import lib.connection as con
from lib.segment import Segment
import lib.segment as segment
import lib.argParser as argParser
import lib.config as config
import socket
import math
import os

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
        if (not os.path.exists(self.path)):
            print(f"[!] File {self.path} not found")
            exit()

        with open(self.path, "rb") as f:
            f.seek(0,2)
            self.fileSize = f.tell()

        self.segment = math.ceil(self.fileSize / (config.SEGMENT_DATA_SIZE))

        print(f"[!] Server is running on {self.ip}:{self.port}")
        print(f"[!] File: {os.path.basename(self.path)} with size {self.fileSize} bytes")
        print(f"[!] Segment: {self.segment} segments")
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

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        print(f"[!] Starting three way handshake with clients...")
        for clients in self.addrList:
            self.three_way_handshake(clients)
            print(f"[!] Starting file transfer with {clients[0]}:{clients[1]}")
            self.file_transfer(clients)


    def file_transfer(self, client_addr):
        # File transfer, server-side, Send file to 1 client
        # N  := window size
        # Sb := sequence base
        # Sm := sequence max

        # window size might be bigger than file size
        # need to check window bound
        windowBound = min(config.WINDOW_SIZE, self.segment)
        seqBase = 0

        # set timeout for file transfer
        self.server.set_timeout(config.TRANSFER_TIMEOUT)

        # send file per segment
        with open(self.path, "rb") as f:
            # Send segment
            for i in range(seqBase, windowBound):
                f.seek(i * config.SEGMENT_DATA_SIZE)
                dataSegment = Segment()
                dataSegment.set_header({"seqNum": i, "ackNum": 0})
                dataSegment.set_payload(f.read(config.SEGMENT_DATA_SIZE))
                self.server.send_data(dataSegment, client_addr)
                print(f"[Segment SEQ={i}] Sent to {client_addr[0]}:{client_addr[1]}")

            while seqBase < self.segment:
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

                for i in range(seqBase, windowBound):
                    f.seek(i * config.SEGMENT_DATA_SIZE)
                    dataSegment = Segment()
                    dataSegment.set_header({"seqNum": i, "ackNum": 0})
                    dataSegment.set_payload(f.read(config.SEGMENT_DATA_SIZE))
                    self.server.send_data(dataSegment, client_addr)
                    print(f"[Segment SEQ={i}] Sent to {client_addr[0]}:{client_addr[1]}")
        
        # initiating four-way handshake to close connection
        # send FIN to client
        # will be sent repeatedly to ensure FIN is received by client
        finAck = False
        dataSegment = Segment()
        dataSegment.set_flag([segment.FIN_FLAG])
        self.server.set_timeout(config.SERVER_TIMEOUT)
        while (not(finAck)):
            try:
                self.server.send_data(dataSegment, client_addr)
                print(f"[!] FIN file transfer sent to {client_addr[0]}:{client_addr[1]}")
                # listen for FIN-ACK
                respFlag = self.server.listen_single_segment()[0].get_flag()
                if (respFlag.FIN and respFlag.ACK):
                    print(f"[!] FIN-ACK file transfer with {client_addr[0]}:{client_addr[1]} success")
                    # sending last ACK to finalize closing connection
                    dataSegment =  Segment()
                    dataSegment.set_flag([segment.ACK_FLAG])
                    self.server.send_data(dataSegment, client_addr)
                    finAck = True
                else:
                    print(f"[!] FIN-ACK file transfer with {client_addr[0]}:{client_addr[1]} failed. Resending FIN...")
            except socket.timeout:
                # ignore FIN-ACK after certain period of time (assume FIN is received)
                # for when client already sends FIN-ACK, yet server does not receive it
                print(f"[!] ACK file transer with {client_addr[0]}:{client_addr[1]} time out. Assuming FIN is received")
                finAck = True


    def three_way_handshake(self, client_addr):
        # Three Way Handshake, server-side as initiator

        # set timeout for handshake
        self.server.set_timeout(config.SERVER_TIMEOUT)

        syn = False
        ack = False
        # will repeatedly send SYN flag until SYN-ACK is received
        while (not(syn)):
            print(f"[!] Server initiating three-way handshake to client {client_addr[0]}:{client_addr[1]}")
            # 1. server sends SYN flag to destined client
            req = Segment()
            req.set_flag([segment.SYN_FLAG])
            self.server.send_data(req, (client_addr))
            try:
                # 2. server waits for client to send SYN-ACK resp
                dataSegment, addr = self.server.listen_single_segment()
                if (not dataSegment.valid_checksum()):
                    print(f"[!] Checksum failed")
                if (dataSegment.get_flag().SYN and dataSegment.get_flag().ACK):
                    syn = True
                else:
                    print(f"[!] Three-way handshake with client {client_addr[0]}:{client_addr[1]} failed")
                    print(f"[!] Restarting handshake...")
            except socket.timeout:
                print(f"[!] Client not responding. Restarting handshake...")

        # will send ACK flag and resend it if SYN-ACK is received again
        while (not(ack)):
            try:
                # 3. server sends ACK on SYN-ACK resp
                ackFlag = Segment()
                ackFlag.set_flag([segment.ACK_FLAG])
                self.server.send_data(ackFlag, (client_addr))
                # 4. server waits for client's response (ACK received or not)
                dataSegment, addr = self.server.listen_single_segment()
                if (not dataSegment.valid_checksum()):
                    print(f"[!] Checksum failed")
                if (dataSegment.get_flag().SYN and dataSegment.get_flag().ACK):
                    print(f"[!] ACK to {client_addr[0]}:{client_addr[1]} failed")
                    print(f"[!] Resending ACK...")
            except socket.timeout:
                print(f"[!] Three-way handshake with client {client_addr[0]}:{client_addr[1]} success")
                ack = True


if __name__ == '__main__':
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()