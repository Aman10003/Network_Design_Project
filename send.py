from socket import *
import numpy as np
from PIL import Image
import pickle  # To serialize NumPy array
import struct  # To attach packet sequence numbers
import random
import error_gen
import time
import checksums  # Import the checksums module

class send:
    def make_packet(self, data_bytes, packet_size, sequence_number):
        """Creates a packet with sequence number and checksum."""
        start = sequence_number * packet_size
        end = start + packet_size
        chunk = data_bytes[start:end]

        # Compute checksum
        checksum = checksums.compute_checksum(chunk)
        print(f"Sender computed checksum: {checksum}")

        # Attach sequence number (2 bytes) + chunk + checksum (2 bytes)
        return struct.pack("!H", sequence_number) + chunk + struct.pack("!H", checksum)


    def adjust_packet_size(self, current_size, loss_rate, ack_delay):
        """Adjust packet size based on loss rate and ACK delay."""
        if loss_rate > 0.1 or ack_delay > 0.1:
            return max(1024, current_size // 2)  # Reduce packet size
        elif loss_rate < 0.01 and ack_delay < 0.05:
            return min(8192, current_size * 2)  # Increase packet size
        return current_size

    def udp_send(self, port: socket, dest, error_type: int, error_rate: float, image: str = 'image/OIP.bmp', window_size: int = 10):
        """Sends an image file over UDP using Go-Back-N protocol."""
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Initialized error_gen
        eg = error_gen.error_gen()

        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets using Go-Back-N with window size {window_size}...")

        # Initialize variables for Go-Back-N
        base = 0
        next_seq_num = 0
        window = {}  # Store packets in the current window
        MAX_RETRIES = 20
        retransmissions = 0
        duplicate_acks = 0

        # Create all packets upfront
        packets = [self.make_packet(data_bytes, packet_size, i) for i in range(total_packets)]

        while base < total_packets:
            # Send packets within the window
            while next_seq_num < base + window_size and next_seq_num < total_packets:
                packet = packets[next_seq_num]

                # Simulate packet errors if needed
                if error_type == 3:
                    packet = eg.packet_error(packet, error_rate)

                # Simulate packet loss
                if error_type == 5 and random.random() < error_rate:
                    print(f">>> Simulating data packet loss for packet {next_seq_num}.")
                else:
                    port.sendto(packet, dest)
                    print(f"Sent packet {next_seq_num}")

                window[next_seq_num] = time.time()  # Track send time
                next_seq_num += 1

            try:
                # Wait for ACK
                port.settimeout(0.5)  # Timeout for ACK
                ack_packet, _ = port.recvfrom(2)  # 2-byte ACK
                ack_num = struct.unpack("!H", ack_packet)[0]

                if ack_num >= base:
                    print(f"Received ACK {ack_num}")
                    base = ack_num + 1  # Slide the window
                    # Remove acknowledged packets from the window
                    for seq in list(window.keys()):
                        if seq <= ack_num:
                            del window[seq]
                else:
                    duplicate_acks += 1
                    print(f"Duplicate ACK {ack_num} received.")

            except timeout:
                # Timeout: Resend all packets in the window
                print(f"Timeout! Resending packets from {base} to {next_seq_num - 1}")
                retransmissions += 1
                for seq in range(base, next_seq_num):
                    packet = packets[seq]
                    port.sendto(packet, dest)

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully!")

        # Compute efficiency metrics
        ack_efficiency = (total_packets / (total_packets + retransmissions)) * 100
        print("\n===== Performance Metrics =====")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print(f"Retransmissions: {retransmissions}")
        print(f"Duplicate ACKs: {duplicate_acks}")
        print("================================\n")