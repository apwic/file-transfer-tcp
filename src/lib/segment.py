from struct import unpack, pack

# Constants 
SYN_FLAG = 0b00000010
ACK_FLAG = 0b00010000
FIN_FLAG = 0b00000001

class SegmentFlag:
    def __init__(self, flag : bytes):
        # Init flag variable from flag byte
        self.SYN = bool(flag & SYN_FLAG)
        self.ACK = bool(flag & ACK_FLAG)
        self.FIN = bool(flag & FIN_FLAG)

    def get_flag_bytes(self) -> bytes:
        # Convert this object to flag in byte form
        flag = 0b00000000
        if self.SYN:
          flag |= SYN_FLAG
        if self.ACK:
          flag |= ACK_FLAG
        if self.FIN:
          flag |= FIN_FLAG

        return pack('>b', flag)

class Segment:
    # -- Internal Function --
    def __init__(self):
        # Initalize segment
        self.seqNum = 0
        self.ackNum = 0
        self.flag = SegmentFlag(0b00000000)
        self.checkSum = 0
        self.dataPayload = b''

    def __str__(self):
        # Optional, override this method for easier print(segmentA)
        return  f"{'Sequence number':24} | {self.seqNum}\n{'Acknowledgement number':24} | {self.ackNum}\n{'Flags':24} | SYN: {self.flag.SYN} ACK: {self.flag.ACK} FIN: {self.flag.FIN}\n{'Checksum':24} | {hex(self.checkSum)}\n{'Valid Checksum':24} | {self.valid_checksum()}\n{'Data Payload':24} | {self.dataPayload}\n"

    def __carry_around_add(self, a, b):
        c = a + b
        return (c & 0xffff)

    def __calculate_checksum(self) -> int:
        # Calculate checksum here, return checksum result
        checkSum = 0x0000

        # start with header
        checkSum = self.__carry_around_add(checkSum, ((self.seqNum & 0xffff0000) >> 16) + (self.seqNum & 0x0000ffff))
        checkSum = self.__carry_around_add(checkSum, ((self.ackNum & 0xffff0000) >> 16) + (self.ackNum & 0x0000ffff))

        # add flag
        checkSum = self.__carry_around_add(checkSum, unpack('>b', self.flag.get_flag_bytes())[0])
        checkSum = self.__carry_around_add(checkSum, self.checkSum)

        # add data
        for i in range(0, len(self.dataPayload), 2):
            temp = self.dataPayload[i:i+2]
            if len(temp) == 1:
                temp += pack('>x')
            checkSum = self.__carry_around_add(checkSum, unpack('>h', temp)[0])
        
        return 0xffff - checkSum


    # -- Setter --
    def set_header(self, header : dict):
        self.seqNum = header['seqNum']
        self.ackNum = header['ackNum']

    def set_payload(self, payload : bytes):
        self.dataPayload = payload

    def set_flag(self, flag_list : list):
        flag = 0b00000000
        for f in flag_list:
            flag |= f
        self.flag = SegmentFlag(flag)


    # -- Getter --
    def get_flag(self) -> SegmentFlag:
        return self.flag

    def get_header(self) -> dict:
        return dict({"seqNum" : self.seqNum, "ackNum" : self.ackNum})

    def get_payload(self) -> bytes:
        return self.dataPayload


    # -- Marshalling --
    def set_from_bytes(self, src : bytes):
        # From pure bytes, unpack() and set into python variable
        header = unpack('>iibxh', src[:12]) # WTF IS THIS???
        self.seqNum = header[0]
        self.ackNum = header[1]
        self.flag = SegmentFlag(header[2])
        self.checkSum = header[3]
        self.dataPayload = src[12:]

    def get_bytes(self) -> bytes:
        # Convert this object to pure bytes
        self.checkSum = self.__calculate_checksum()
        return pack('>ii', self.seqNum, self.ackNum) + self.flag.get_flag_bytes() + pack('>xH', self.checkSum) + self.dataPayload


    # -- Checksum --
    def valid_checksum(self) -> bool:
        # Use __calculate_checksum() and check integrity of this object
        return self.__calculate_checksum() == 0x0000
