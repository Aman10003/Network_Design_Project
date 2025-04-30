import socket
import struct
import time
from checksums import compute_checksum

FLAG_SYN = 0x01
FLAG_ACK = 0x02
FLAG_FIN = 0x04

class TCPSegment:
    """
    Simple TCP‐style header:
     - flags: 1 byte
     - seq:   4 bytes
     - ack:   4 bytes
     - win:   2 bytes
     - csum:  2 bytes
    """

    _HDR_FMT = "!BIIHH"         # flags, seq, ack, win, checksum
    _HDR_LEN = struct.calcsize(_HDR_FMT)

    def __init__(self, flags, seq, ack, win, data=b""):
        self.flags = flags
        self.seq   = seq
        self.ack   = ack
        self.win   = win
        self.data  = data

    def pack(self):
        # pack header without checksum, then append actual checksum
        hdr_wo_ck = struct.pack("!BIIH",
                                self.flags,
                                self.seq,
                                self.ack,
                                self.win)
        ck = compute_checksum(hdr_wo_ck + self.data)
        return hdr_wo_ck + struct.pack("!H", ck) + self.data

    @classmethod
    def unpack(cls, raw):
        if len(raw) < cls._HDR_LEN:
            raise ValueError("Segment too short")
        flags, seq, ack, win, ck = struct.unpack(cls._HDR_FMT, raw[:cls._HDR_LEN])
        data = raw[cls._HDR_LEN:]
        # verify checksum
        hdr_wo_ck = raw[:cls._HDR_LEN-2]
        if compute_checksum(hdr_wo_ck + data) != ck:
            raise ValueError("Checksum mismatch")
        return cls(flags, seq, ack, win, data)


class TCPSender:
    def __init__(self, sock: socket.socket, peer_addr, mss=1024):
        self.sock     = sock
        self.peer     = peer_addr
        self.mss      = mss
        self.cwnd     = 1
        self.ssthresh = 16
        self.alpha    = 0.125
        self.beta     = 0.25
        self.ERTT     = 0.1
        self.DevRTT   = 0.05

    def _rto(self):
        return max(0.1, self.ERTT + 4*self.DevRTT)

    def connect(self):
        # Active open
        syn = TCPSegment(FLAG_SYN, 0, 0, 0).pack()
        self.sock.sendto(syn, self.peer)
        self.sock.settimeout(1.0)

        raw, _ = self.sock.recvfrom(4096)
        synack = TCPSegment.unpack(raw)
        if synack.flags & FLAG_SYN and synack.flags & FLAG_ACK:
            # reply final ACK
            ack = TCPSegment(FLAG_ACK, 1, synack.seq+1, 0).pack()
            self.sock.sendto(ack, self.peer)
        else:
            raise RuntimeError("Handshake failed")

    def send(self, data: bytes):
        # Simplified sliding‐window + timeout + basic Tahoe
        base = 0
        next_seq = 0
        window = {}  # seq → (time_sent, raw_segment)

        total = len(data)
        while base < total:
            # fill window
            while next_seq < base + self.cwnd*self.mss and next_seq < total:
                chunk = data[next_seq: next_seq+self.mss]
                seg   = TCPSegment(FLAG_ACK, next_seq, 0, 0, chunk).pack()
                self.sock.sendto(seg, self.peer)
                window[next_seq] = (time.time(), seg)
                next_seq += len(chunk)

            # wait for ACK or timeout
            try:
                self.sock.settimeout(self._rto())
                raw, _ = self.sock.recvfrom(4096)
                ackseg = TCPSegment.unpack(raw)
                if ackseg.flags & FLAG_ACK:
                    acknum = ackseg.ack
                    if acknum > base:
                        sample = time.time() - window[base][0]
                        # update RTT estimators
                        self.ERTT   = (1-self.alpha)*self.ERTT + self.alpha*sample
                        self.DevRTT = (1-self.beta)*self.DevRTT + self.beta*abs(sample - self.ERTT)
                        # congestion control
                        if self.cwnd < self.ssthresh:
                            self.cwnd += 1            # slow start
                        else:
                            self.cwnd += 1/self.cwnd  # congestion avoidance
                        base = acknum
            except socket.timeout:
                # timeout → Tahoe
                self.ssthresh = max(self.cwnd/2, 1)
                self.cwnd     = 1
                # retransmit
                self.sock.sendto(window[base][1], self.peer)

        # initiate teardown
        fin = TCPSegment(FLAG_FIN, total, 0, 0).pack()
        self.sock.sendto(fin, self.peer)
        # could wait for FIN‐ACK here…

    def close(self):
        # placeholder for any cleanup
        pass


class TCPReceiver:
    def __init__(self, sock: socket.socket, peer_addr):
        self.sock      = sock
        self.peer      = peer_addr
        self.expected  = 0
        self.buffer    = {}

    def listen(self):
        # Passive open: wait for SYN
        raw, addr = self.sock.recvfrom(4096)
        syn = TCPSegment.unpack(raw)
        if syn.flags & FLAG_SYN:
            # send SYN-ACK
            synack = TCPSegment(FLAG_SYN|FLAG_ACK, 0, syn.seq+1, 0).pack()
            self.sock.sendto(synack, addr)
            # wait for ACK
            raw2, _ = self.sock.recvfrom(4096)
            ack = TCPSegment.unpack(raw2)
            if ack.flags & FLAG_ACK:
                self.expected = ack.ack

    def recv(self):
        data_parts = []
        while True:
            raw, _ = self.sock.recvfrom(4096)
            seg = TCPSegment.unpack(raw)
            if seg.flags & FLAG_FIN:
                # send final ACK
                finack = TCPSegment(FLAG_ACK, 0, seg.seq+1, 0).pack()
                self.sock.sendto(finack, self.peer)
                break

            if seg.seq == self.expected:
                data_parts.append(seg.data)
                self.expected += len(seg.data)

            # always ACK highest in‐order byte
            ack = TCPSegment(FLAG_ACK, 0, self.expected, 0).pack()
            self.sock.sendto(ack, self.peer)

        return b"".join(data_parts)
