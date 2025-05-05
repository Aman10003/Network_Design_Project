import socket
import struct
import time
import pickle
import numpy as np
from PIL import Image
from io import BytesIO
from checksums import compute_checksum

# TCP Flags
FLAG_SYN = 0x01
FLAG_ACK = 0x02
FLAG_FIN = 0x04
FLAG_RST = 0x08  # Reset flag for abrupt connection termination


class TCPSegment:
    """
    TCP segment header format:
     - flags: 1 byte (SYN, ACK, FIN, RST)
     - seq: 4 bytes (sequence number)
     - ack: 4 bytes (acknowledgment number)
     - win: 2 bytes (window size)
     - csum: 2 bytes (checksum)
    """
    _HDR_FMT = "!BIIHH"  # flags, seq, ack, win, checksum
    _HDR_LEN = struct.calcsize(_HDR_FMT)

    def __init__(self, flags, seq, ack, win, data=b""):
        self.flags = flags
        self.seq = seq
        self.ack = ack
        self.win = win
        self.data = data

    def pack(self):
        # Pack header without checksum, then append actual checksum
        hdr_wo_ck = struct.pack("!BIIH",
                                self.flags,
                                self.seq,
                                self.ack,
                                self.win)
        ck = compute_checksum(hdr_wo_ck + self.data)
        print(f"Calculated checksum: {ck}")
        return hdr_wo_ck + struct.pack("!H", ck) + self.data

    @classmethod
    def unpack(cls, raw):
        if len(raw) < cls._HDR_LEN:
            raise ValueError("Segment too short")
        flags, seq, ack, win, ck = struct.unpack(cls._HDR_FMT, raw[:cls._HDR_LEN])
        data = raw[cls._HDR_LEN:]
        # Verify checksum
        hdr_wo_ck = raw[:cls._HDR_LEN - 2]
        if compute_checksum(hdr_wo_ck + data) != ck:
            raise ValueError("Checksum mismatch")
        print(f"Received checksum: {ck}, Computed checksum: {compute_checksum(hdr_wo_ck + data)}")
        return cls(flags, seq, ack, win, data)


class TCPSender:
    def __init__(self, sock: socket.socket, peer_addr, mss=1024):
        self.sock = sock
        self.peer = peer_addr
        self.mss = mss
        self.cwnd = 1  # Congestion window (in MSS units)
        self.ssthresh = 16  # Slow start threshold
        self.rwnd = 16  # Receiver's advertised window
        self.alpha = 0.125  # EWMA weight for RTT
        self.beta = 0.25  # EWMA weight for deviation
        self.ERTT = 0.1  # Estimated RTT (initial value)
        self.DevRTT = 0.05  # RTT deviation (initial value)
        self.dup_acks = 0  # Count of duplicate ACKs
        self.last_ack = 0  # Last ACK received
        self.congestion_state = "slow_start"  # Current congestion state
        self.fin_sent = False  # Flag to track if FIN has been sent
        self.fin_acked = False  # Flag to track if FIN has been ACKed
        self.next_seq = 0 # Track the next sequence number

        # Add data collection lists
        self.time_points = []  # Time points for all measurements
        self.cwnd_values = []  # Congestion window values
        self.rtt_samples = []  # RTT sample values
        self.rto_values = []  # RTO values
        self.start_time = time.time()  # Reference start time

    def load_image_bytes(self, data):
        """
        Convert data to pickled bytes for transmission.
        If data is already bytes, it's assumed to be a file and is pickled directly.
        If data is a path to an image, it's loaded, converted to a NumPy array, and pickled.
        """
        if isinstance(data, bytes):
            # Data is already in bytes format, pickle it
            try:
                # Try to load as an image first
                img = Image.open(BytesIO(data))
                numpydata = np.asarray(img)
                return pickle.dumps(numpydata)
            except:
                # If that fails, just pickle the raw bytes
                return pickle.dumps(data)
        elif isinstance(data, str):
            # Data is a path to an image
            img = Image.open(data)
            numpydata = np.asarray(img)
            return pickle.dumps(numpydata)
        else:
            # Data is something else, try to pickle it directly
            return pickle.dumps(data)

    def _rto(self):
        """Calculate Retransmission Timeout using TCP's standard formula"""
        rto = max(0.1, self.ERTT + 4 * self.DevRTT)

        # Record RTO value
        current_time = time.time() - self.start_time
        self.time_points.append(current_time)
        self.rto_values.append(rto)

        return rto

    def connect(self):
        """Perform active open (client-side 3-way handshake)"""
        # Send SYN
        syn = TCPSegment(FLAG_SYN, self.next_seq, 0, self.rwnd).pack()
        self.sock.sendto(syn, self.peer)
        self.sock.settimeout(1.0)
        print("TCP: SYN sent")

        # Wait for SYN-ACK
        try:
            raw, _ = self.sock.recvfrom(4096)
            synack = TCPSegment.unpack(raw)
            if synack.flags & FLAG_SYN and synack.flags & FLAG_ACK:
                # Update receiver window based on peer's advertised window
                self.rwnd = synack.win
                # Send final ACK
                self.next_seq += 1  # Increment sequence number
                ack = TCPSegment(FLAG_ACK, self.next_seq, synack.seq + 1, self.rwnd).pack()
                self.sock.sendto(ack, self.peer)
                print("TCP: Connection established (3-way handshake complete)")
                return True
            else:
                raise RuntimeError("Handshake failed: No SYN-ACK received")
        except socket.timeout:
            raise RuntimeError("Handshake failed: Timeout waiting for SYN-ACK")

    def send(self, data):
        """Send data using TCP with congestion control"""
        # Pickle the data for transmission
        pickled_data = self.load_image_bytes(data)

        # Debug: Save pickled data to a file
        with open("debug_pickled_data.bin", "wb") as f:
            f.write(pickled_data)

        base = self.next_seq # Start from current sequence number
        next_seq = self.next_seq
        window = {}  # seq → (time_sent, raw_segment)

        total = len(pickled_data)
        print(f"TCP: Sending {total} bytes of pickled data")

        if self.rwnd == 0:
            # Zero window - send a probe packet after a timeout
            print("TCP: Zero window detected, waiting for window update")
            time.sleep(self._rto())
            # Send a 1-byte probe if window is still zero
            if next_seq > 0:
                probe_seq = max(0, next_seq - 1)
                probe_data = pickled_data[probe_seq:probe_seq + 1] if probe_seq < total else b''
                probe = TCPSegment(FLAG_ACK, probe_seq, 0, 0, probe_data).pack()
                self.sock.sendto(probe, self.peer)
                print("TCP: Sent zero window probe")

        while base < total:
            # Fill window based on min(cwnd, rwnd)
            effective_window = min(self.cwnd * self.mss, self.rwnd)
            while next_seq < base + effective_window and next_seq < total:
                chunk = pickled_data[next_seq: next_seq + self.mss]
                seg = TCPSegment(FLAG_ACK, next_seq, 0, self.rwnd, chunk).pack()
                self.sock.sendto(seg, self.peer)
                window[next_seq] = (time.time(), seg)
                print(f"TCP: Sent data segment, seq={next_seq}, len={len(chunk)}")
                next_seq += len(chunk)

            # Wait for ACK or timeout
            try:
                self.sock.settimeout(self._rto())
                raw, _ = self.sock.recvfrom(4096)
                ackseg = TCPSegment.unpack(raw)

                if ackseg.flags & FLAG_ACK:
                    acknum = ackseg.ack
                    # Update receiver window
                    self.rwnd = ackseg.win

                    if acknum > base:
                        # New ACK received
                        # Check if base exists in window before calculating RTT
                        if base in window:
                            sample = time.time() - window[base][0]
                            # Update RTT estimators
                            self.ERTT = (1 - self.alpha) * self.ERTT + self.alpha * sample
                            self.DevRTT = (1 - self.beta) * self.DevRTT + self.beta * abs(sample - self.ERTT)
                            print(f"TCP: RTT sample={sample:.4f}s, ERTT={self.ERTT:.4f}s, DevRTT={self.DevRTT:.4f}s")

                        # Reset duplicate ACK counter
                        self.dup_acks = 0
                        self.last_ack = acknum

                        # Congestion control - handle new ACK
                        if self.congestion_state == "slow_start":
                            self.cwnd += 1  # Exponential growth
                            print(f"TCP: Slow Start - cwnd increased to {self.cwnd}")
                            if self.cwnd >= self.ssthresh:
                                self.congestion_state = "congestion_avoidance"
                                print(f"TCP: Entering Congestion Avoidance, ssthresh={self.ssthresh}")

                        elif self.congestion_state == "congestion_avoidance":
                            self.cwnd += 1 / self.cwnd  # Linear growth
                            print(f"TCP: Congestion Avoidance - cwnd={self.cwnd:.2f}")

                        elif self.congestion_state == "fast_recovery":
                            # Exit fast recovery
                            self.cwnd = self.ssthresh
                            self.congestion_state = "congestion_avoidance"
                            print(f"TCP: Exiting Fast Recovery - cwnd={self.cwnd}")

                        # Remove acknowledged packets from window
                        for seq in list(window.keys()):
                            if seq < acknum:
                                del window[seq]

                        base = acknum

                    elif acknum == self.last_ack:
                        # Duplicate ACK
                        self.dup_acks += 1
                        print(f"TCP: Duplicate ACK #{self.dup_acks} for seq={acknum}")

                        # Fast Retransmit and Fast Recovery (TCP Reno)
                        if self.dup_acks == 3:
                            print("TCP: Triple duplicate ACK - Fast Retransmit")
                            # Retransmit the missing segment
                            if base in window:
                                self.sock.sendto(window[base][1], self.peer)
                                print(f"TCP: Fast retransmit for seq={base}")

                            # TCP Reno - Fast Recovery
                            self.ssthresh = max(self.cwnd / 2, 2)
                            self.cwnd = self.ssthresh + 3  # Inflate for the 3 duplicate ACKs
                            self.congestion_state = "fast_recovery"
                            print(f"TCP: Entering Fast Recovery - ssthresh={self.ssthresh}, cwnd={self.cwnd}")

                        elif self.congestion_state == "fast_recovery":
                            # Inflate cwnd for each additional duplicate ACK
                            self.cwnd += 1
                            print(f"TCP: Fast Recovery - cwnd inflated to {self.cwnd}")

                    # Inside the send loop, when cwnd changes:
                    # For example, after line 162, 169, 175, 201, 206, 215
                    current_time = time.time() - self.start_time
                    self.time_points.append(current_time)
                    self.cwnd_values.append(self.cwnd)

                    # When RTT sample is calculated (around line 149-153)
                    if base in window:
                        sample = time.time() - window[base][0]
                        current_time = time.time() - self.start_time
                        self.time_points.append(current_time)
                        self.rtt_samples.append(sample)

            except socket.timeout:
                # Timeout - implement TCP Tahoe
                print("TCP: Timeout detected")
                self.ssthresh = max(self.cwnd / 2, 2)
                self.cwnd = 1
                self.dup_acks = 0
                self.congestion_state = "slow_start"
                print(f"TCP: Timeout - Tahoe reset, ssthresh={self.ssthresh}, cwnd={self.cwnd}")

                # Retransmit the lost segment
                if base in window:
                    self.sock.sendto(window[base][1], self.peer)
                    print(f"TCP: Retransmitting seq={base} after timeout")

        # Initiate connection teardown
        self.close()

    def close(self):
        """Perform active close (4-way handshake)"""
        if self.fin_sent:
            return

        # Send FIN
        fin = TCPSegment(FLAG_FIN, 0, 0, self.rwnd).pack()
        self.sock.sendto(fin, self.peer)
        self.fin_sent = True
        print("TCP: FIN sent, initiating connection teardown")

        # Wait for ACK of FIN
        try:
            self.sock.settimeout(2.0)
            raw, _ = self.sock.recvfrom(4096)
            ack = TCPSegment.unpack(raw)

            if ack.flags & FLAG_ACK:
                print("TCP: Received ACK for FIN")
                self.fin_acked = True

            # Wait for FIN from peer
            if not (ack.flags & FLAG_FIN):
                raw, _ = self.sock.recvfrom(4096)
                fin = TCPSegment.unpack(raw)

                if fin.flags & FLAG_FIN:
                    print("TCP: Received FIN from peer")
                    # Send ACK for the FIN
                    final_ack = TCPSegment(FLAG_ACK, 0, fin.seq + 1, self.rwnd).pack()
                    self.sock.sendto(final_ack, self.peer)
                    print("TCP: Sent final ACK, connection closed")
            else:
                # Combined FIN-ACK received
                print("TCP: Received FIN-ACK")
                # Send ACK for the FIN
                final_ack = TCPSegment(FLAG_ACK, 0, ack.seq + 1, self.rwnd).pack()
                self.sock.sendto(final_ack, self.peer)
                print("TCP: Sent final ACK, connection closed")

        except socket.timeout:
            print("TCP: Timeout during connection teardown, assuming closed")


class TCPReceiver:
    def __init__(self, sock: socket.socket, peer_addr, buffer_size=65536):
        self.sock = sock
        self.peer = peer_addr
        self.expected = 0  # Next expected sequence number
        self.buffer = {}  # Buffer for out-of-order segments
        self.rwnd = 16  # Receiver window size (in MSS units)
        self.mss = 1024  # Maximum segment size
        self.buffer_size = buffer_size  # Total buffer size in bytes
        self.fin_received = False
        self.fin_seq = 0

    def unpickle_data(self, data_parts):
        """
        Unpickle the received data.
        """
        # Join all data parts
        joined_data = b"".join(data_parts)

        # Debug: Save reassembled data to a file
        with open("debug_reassembled_data.bin", "wb") as f:
            f.write(joined_data)

        print(f"TCP: Unpickling {len(joined_data)} bytes of data")

        # First, check if the data starts with the pickle protocol marker
        if joined_data and joined_data[0] in (0x80, 0x81, 0x82, 0x83, 0x84, 0x85):
            try:
                # Unpickle the data
                unpickled_data = pickle.loads(joined_data)

                # Debug: Save unpickled data to a file
                with open("debug_unpickled_data.bin", "wb") as f:
                    f.write(pickle.dumps(unpickled_data))

                print("TCP: Data unpickled successfully")

                # If it's a NumPy array, convert it back to bytes for compatibility
                if isinstance(unpickled_data, np.ndarray):
                    print("TCP: Converting NumPy array to image bytes")
                    img = Image.fromarray(unpickled_data)
                    img_bytes = BytesIO()
                    img.save(img_bytes, format="BMP")
                    return img_bytes.getvalue()

                return unpickled_data
            except pickle.UnpicklingError as e:
                print(f"TCP: Pickle unpickling error: {e}")
                # If it's a specific unpickling error, return the raw data
                return joined_data
            except Exception as e:
                print(f"TCP: Error during unpickling: {e}")
                # For any other exception, return the raw data
                return joined_data
        else:
            # If the data doesn't start with a pickle protocol marker, it's likely raw data
            print("TCP: Data doesn't appear to be pickled, returning raw data")
            return joined_data

    def listen(self):
        """Perform passive open (server-side 3-way handshake)"""
        # Wait for SYN
        raw, addr = self.sock.recvfrom(4096)
        syn = TCPSegment.unpack(raw)

        if syn.flags & FLAG_SYN:
            print("TCP: Received SYN")
            # Send SYN-ACK
            synack = TCPSegment(FLAG_SYN | FLAG_ACK, 0, syn.seq + 1, self.rwnd * self.mss).pack()
            self.sock.sendto(synack, addr)
            print("TCP: Sent SYN-ACK")

            # Wait for ACK
            raw2, _ = self.sock.recvfrom(4096)
            ack = TCPSegment.unpack(raw2)

            if ack.flags & FLAG_ACK:
                print("TCP: Received ACK, connection established")
                self.expected = ack.ack
                return True
            else:
                print("TCP: Handshake failed - final ACK not received")
                return False
        else:
            print("TCP: Handshake failed - SYN not received")
            return False

    def recv(self):
        """Receive data with proper buffering and flow control"""
        data_parts = []
        max_attempts = 3  # Maximum number of consecutive timeouts
        timeout_attempts = 0
        last_data_time = time.time()  # Track when we last received data

        while not self.fin_received:
            try:
                self.sock.settimeout(10.0)
                raw, _ = self.sock.recvfrom(4096)
                timeout_attempts = 0  # Reset timeout counter on successful receive
                last_data_time = time.time()  # Update last data time

                seg = TCPSegment.unpack(raw)

                # Check for FIN flag
                if seg.flags & FLAG_FIN:
                    print("TCP: Received FIN")
                    self.fin_received = True
                    self.fin_seq = seg.seq

                    # Send ACK for FIN
                    finack = TCPSegment(FLAG_ACK | FLAG_FIN, 0, seg.seq + 1, self.rwnd * self.mss).pack()
                    self.sock.sendto(finack, self.peer)
                    print("TCP: Sent FIN-ACK")

                    # Wait for final ACK
                    try:
                        self.sock.settimeout(2.0)
                        raw, _ = self.sock.recvfrom(4096)
                        final_ack = TCPSegment.unpack(raw)
                        if final_ack.flags & FLAG_ACK:
                            print("TCP: Received final ACK, connection closed")
                    except socket.timeout:
                        print("TCP: Receive timeout waiting for final ACK, assuming connection closed")

                    break

                # Process data segment
                if seg.seq == self.expected:
                    # In-order segment
                    print(f"TCP: Received in-order segment, seq={seg.seq}, len={len(seg.data)}")
                    data_parts.append(seg.data)
                    self.expected += len(seg.data)

                    # Check if we have buffered segments that can now be processed
                    while self.expected in self.buffer:
                        data_parts.append(self.buffer[self.expected])
                        print(f"TCP: Using buffered segment, seq={self.expected}")
                        next_seq = self.expected + len(self.buffer[self.expected])
                        del self.buffer[self.expected]
                        self.expected = next_seq

                elif seg.seq > self.expected:
                    # Out-of-order segment, buffer it
                    print(f"TCP: Received out-of-order segment, seq={seg.seq}, expected={self.expected}")
                    self.buffer[seg.seq] = seg.data

                # Update receiver window based on available buffer space
                used_buffer = sum(len(data) for data in self.buffer.values()) + sum(len(data) for data in data_parts)

                # Ensure window size doesn't exceed maximum value
                available_buffer = max(0, self.buffer_size - used_buffer)
                if self.rwnd == 0 and available_buffer > self.mss:
                    print("TCP: Window opened after being closed")

                self.rwnd = min(65535 // self.mss, max(1, available_buffer // self.mss))

                # When sending ACK
                window_size = min(65535, self.rwnd * self.mss)  # Ensure it doesn't exceed 65535
                ack = TCPSegment(FLAG_ACK, 0, self.expected, window_size).pack()

                self.sock.sendto(ack, self.peer)
                print(f"TCP: Sent ACK={self.expected}, window={self.rwnd}")

            except socket.timeout:
                timeout_attempts += 1
                print(f"TCP: Receive timeout ({timeout_attempts}/{max_attempts})")

                # If we've received some data and hit multiple timeouts, assume transfer is complete
                if data_parts and timeout_attempts >= max_attempts:
                    print(f"TCP: Multiple timeouts after receiving data, assuming transfer complete")
                    print(f"TCP: Returning {sum(len(d) for d in data_parts)} bytes received so far")
                    return self.unpickle_data(data_parts)

                # If it's been a long time since we received any data, assume transfer is complete
                if data_parts and time.time() - last_data_time > 30:  # 30 seconds without data
                    print(f"TCP: No data received for 30 seconds, assuming transfer complete")
                    print(f"TCP: Returning {sum(len(d) for d in data_parts)} bytes received so far")
                    return self.unpickle_data(data_parts)

                # If we've never received any data and hit max timeouts, raise exception
                if not data_parts and timeout_attempts >= max_attempts:
                    raise RuntimeError("TCP: Failed to receive any data after multiple attempts")

                # Otherwise, continue trying to receive
                continue

            except Exception as e:
                print(f"TCP: Error during receive: {e}")
                if data_parts:
                    print(f"TCP: Returning {sum(len(d) for d in data_parts)} bytes received so far")
                    return self.unpickle_data(data_parts)
                raise  # Re-raise if no data received

        # Return the reassembled data
        return self.unpickle_data(data_parts)
