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

    def __init__(self):
        self.progress_bar = None
        self.retrans_label = None
        self.dup_ack_label = None
        self.ack_eff_label = None
        self.retrans_overhead_label = None

    def make_packet(self, data_bytes, packet_size, sequence_number):
        """Creates a packet with sequence number and checksum."""
        start = sequence_number * packet_size
        end = start + packet_size

        # Optionally override start with a provided start_index (for dynamic sizing)
        if hasattr(self, 'custom_start_index'):
            start = self.custom_start_index
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

    def udp_send(self, port: socket, dest, error_type: int, error_rate: float, image: str = 'image/OIP.bmp',
                 update_ui_callback=None, use_gbn=False, window_size=10):

        """Sends an image file over UDP with RDT 3.0 and adaptive timeout."""
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Initialized error_gen
        eg = error_gen.error_gen()

        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets...")

        # Initial timeout values
        ERTT = 0.05  # Estimated RTT
        DevRTT = 0.01  # Deviation of RTT
        alpha = 0.125
        beta = 0.25

        sequence_number = 0
        MAX_RETRIES = 20

        if use_gbn:
            base = 0
            next_seq_num = 0
            window = {}  # Store packets for retransmission
            packet_timestamps = {}  # Track send times for RTT

        retransmissions = 0  # Count packet retransmissions
        duplicate_acks = 0  # Count duplicate ACKs
        total_acks_received = 0  # Track total ACKs received
        unique_acks_received = set()  # Track unique ACKs received
        total_acks_sent = 0  # Initialize total ACKs sent

        # Initalize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label, self.retrans_overhead_label] = update_ui_callback


        while sequence_number < total_packets:
            self.custom_start_index = start_index
            packet = self.make_packet(data_bytes, packet_size, sequence_number)
            retries = 0

            while retries < MAX_RETRIES:
                try:
                    # Introduce packet errors if needed
                    packet_modified = packet
                    if error_type == 3:
                        packet_modified = eg.packet_error(packet, error_rate)

                    start_time = time.time()

                    # Simulate data packet loss
                    if error_type == 5 and random.random() < error_rate:
                        print(f">>> Simulating data packet loss for packet {sequence_number}.")
                    else:
                        # Send packet
                        port.sendto(packet_modified, dest)
                        print(f"Sent packet {sequence_number} (size: {packet_size} bytes)")

                    # Wait for ACK
                    port.settimeout(ERTT + 4 * DevRTT)  # Adaptive timeout
                    # port.settimeout(0.5)  # Non-adaptive timeout. Adaptive timeout doesn't work
                    print(f"Timeout is now {ERTT + 4 * DevRTT:.4f} seconds")

                    ack_packet, _ = port.recvfrom(2)  # 2-byte ACK
                    end_time = time.time()

                    RTT = end_time - start_time
                    ack_num = struct.unpack("!H", ack_packet)[0]
                    total_acks_received += 1  # Track total ACKs received

                    if ack_num not in unique_acks_received:
                        unique_acks_received.add(ack_num)
                    else:
                        duplicate_acks += 1  # Count duplicate ACKs

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received. Sending next packet.")

                        # Advance data pointer for next packet
                        start_index += packet_size

                        # Update timeout estimates
                        ERTT = (1 - alpha) * ERTT + alpha * RTT
                        DevRTT = (1 - beta) * DevRTT + beta * abs(RTT - ERTT)

                        # Dynamically adjust packet size
                        loss_rate = retransmissions / (sequence_number + 1)
                        new_packet_size = self.adjust_packet_size(packet_size, loss_rate, RTT)
                        if new_packet_size != packet_size:
                            print(f"Adjusted packet size from {packet_size} to {new_packet_size}")
                        packet_size = new_packet_size

                        sequence_number += 1

                        # def update_progress(self, progress, retransmissions, duplicate_acks, ack_efficiency=0, retransmission_overhead=0):
                        if update_ui_callback is not None:
                            # Update UI progress **only after successful transmission**
                            progress = sequence_number / total_packets
                            self.update_progress(progress, retransmissions, duplicate_acks)

                        break #Exit retry loop

                    else:
                        print(f"Incorrect ACK {ack_num}, expecting {sequence_number}. Retrying.")
                        duplicate_acks += 1

                except timeout:
                    retries += 1
                    retransmissions += 1
                    print(f"Timeout for packet {sequence_number}. Retries: {retries}")

            if retries == MAX_RETRIES:
                print(f"Failed to send packet {sequence_number} after {MAX_RETRIES} retries.")
                return total_packets, retransmissions, duplicate_acks

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully!")

        # Compute efficiency metrics
        ack_efficiency = (len(unique_acks_received) / total_acks_received) * 100 if total_acks_received > 0 else 0
        retransmission_overhead = (retransmissions / total_packets) * 100 if total_packets > 0 else 0

        print("\n===== Performance Metrics =====")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print(f"Retransmission Overhead: {retransmission_overhead:.2f}%")
        print("================================\n")


        # -----------------------------------------------
        # GBN Mode (Only runs if use_gbn is True)
        # -----------------------------------------------
        if use_gbn:
            base = 0
            next_seq_num = 0
            window = {}
            packet_timestamps = {}

            while base < total_packets:
                # Send packets in the window
                while next_seq_num < base + window_size and next_seq_num < total_packets:
                    packet = self.make_packet(data_bytes, packet_size, next_seq_num)
                    if error_type == 3:
                        packet = eg.packet_error(packet, error_rate)

                    port.sendto(packet, dest)
                    print(f"Sent packet {next_seq_num} (GBN mode)")
                    window[next_seq_num] = packet
                    packet_timestamps[next_seq_num] = time.time()
                    next_seq_num += 1

                try:
                    port.settimeout(ERTT + 4 * DevRTT)
                    ack_packet, _ = port.recvfrom(2)
                    ack_num = struct.unpack("!H", ack_packet)[0]
                    end_time = time.time()

                    RTT = end_time - min(packet_timestamps.values())
                    total_acks_received += 1

                    if ack_num not in unique_acks_received:
                        unique_acks_received.add(ack_num)
                    else:
                        duplicate_acks += 1

                    if ack_num >= base:
                        print(f"Received cumulative ACK {ack_num}")
                        for seq in list(window):
                            if seq <= ack_num:
                                del window[seq]
                                del packet_timestamps[seq]
                        base = ack_num + 1

                        # Update RTT estimates
                        ERTT = (1 - alpha) * ERTT + alpha * RTT
                        DevRTT = (1 - beta) * DevRTT + beta * abs(RTT - ERTT)

                        # Dynamically adjust packet size
                        loss_rate = retransmissions / (base + 1)
                        new_packet_size = self.adjust_packet_size(packet_size, loss_rate, RTT)
                        if new_packet_size != packet_size:
                            print(f"Adjusted packet size from {packet_size} to {new_packet_size}")
                        packet_size = new_packet_size

                        if update_ui_callback is not None:
                            progress = base / total_packets
                            self.update_progress(progress, retransmissions, duplicate_acks)

                except timeout:
                    print(f"Timeout at base {base}. Retransmitting window...")
                    for seq, pkt in window.items():
                        port.sendto(pkt, dest)
                        retransmissions += 1

            # GBN completion
            port.sendto(b'END', dest)
            print("Image data sent successfully! [GBN Mode]")

            ack_efficiency = (len(unique_acks_received) / total_acks_received) * 100 if total_acks_received > 0 else 0
            retransmission_overhead = (retransmissions / total_packets) * 100 if total_packets > 0 else 0

            print("\n===== GBN Performance Metrics =====")
            print(f"ACK Efficiency: {ack_efficiency:.2f}%")
            print(f"Retransmission Overhead: {retransmission_overhead:.2f}%")
            print("====================================\n")

        return total_packets, retransmissions, duplicate_acks, ack_efficiency, retransmission_overhead



    # Cdoe to attempt to update the gui
    def update_progress(self, progress, retransmissions, duplicate_acks, ack_efficiency=0, retransmission_overhead=0):
        """Update UI dynamically."""
        self.progress_bar.set_value(progress)
        self.retrans_label.set_text(f"Retransmissions: {retransmissions}")
        self.dup_ack_label.set_text(f"Duplicate ACKs: {duplicate_acks}")
        self.ack_eff_label.set_text(f"ACK Efficiency: {ack_efficiency:.2f}")
        self.retrans_overhead_label.set_text(f"Retransmission Overhead: {retransmission_overhead:.2f}")
