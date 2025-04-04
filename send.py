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

    def udp_send(self, port: socket, dest, error_type: int, error_rate: float, image: str = 'image/OIP.bmp', update_ui_callback = None):
        """RDT 3.0 with adaptive timeout implementation."""
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

        retransmissions = 0  # Count packet retransmissions
        duplicate_acks = 0  # Count duplicate ACKs
        total_acks_received = 0  # Track total ACKs received
        unique_acks_received = set()  # Track unique ACKs received
        total_acks_sent = 0  # Initialize total ACKs sent

        # Initialize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label,
             self.retrans_overhead_label] = update_ui_callback

        while sequence_number < total_packets:
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
                        print(f"Sent packet {sequence_number}")

                    # Wait for ACK
                    # port.settimeout(ERTT + 4 * DevRTT)  # Adaptive timeout
                    port.settimeout(0.5)  # Non-adaptive timeout. Adaptive timeout doesn't work

                    print(f"Timeout is now {ERTT + 4 * DevRTT}")
                    ack_packet, _ = port.recvfrom(2)  # 2-byte ACK
                    end_time = time.time()

                    ack_num = struct.unpack("!H", ack_packet)[0]
                    total_acks_received += 1  # Track total ACKs received
                    total_acks_sent += 1  # Increment total ACKs sent for efficiency metric

                    if ack_num not in unique_acks_received:
                        unique_acks_received.add(ack_num)
                    else:
                        duplicate_acks += 1  # Count duplicate ACKs

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received. Sending next packet.")
                        sequence_number += 1  # Only increment on correct ACK

                        if update_ui_callback is not None:
                            # Update UI progress **only after successful transmission**
                            progress = sequence_number / total_packets
                            update_ui_callback(progress, retransmissions, duplicate_acks)

                        # Calculate RTT and update ERTT and DevRTT
                        RTT = end_time - start_time
                        ERTT = (1 - alpha) * ERTT + alpha * RTT
                        DevRTT = (1 - beta) * DevRTT + beta * abs(RTT - ERTT)

                        break  # Exit retry loop

                    else:
                        duplicate_acks += 1  # Track duplicate ACKs
                        print(f"Incorrect ACK {ack_num}. Retransmitting packet {sequence_number}...")

                except timeout:
                    retries += 1
                    retransmissions += 1  # Track retransmissions
                    print(f"Timeout for packet {sequence_number}. Retries: {retries}")

            if retries == MAX_RETRIES:
                print(f"Failed to send packet {sequence_number} after {MAX_RETRIES} retries.")
                return total_packets, retransmissions, duplicate_acks

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully using RDT 3.0!")

        # Compute efficiency metrics
        ack_efficiency = (len(unique_acks_received) / total_acks_received) * 100 if total_acks_received > 0 else 0
        print("\n===== Performance Metrics =====")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print(f"Retransmission Overhead: {(retransmissions / total_packets) * 100:.2f}%")
        print("================================\n")

        return total_packets, retransmissions, duplicate_acks, ack_efficiency, (retransmissions / total_packets) * 100

    def udp_send_gbn(self, port: socket, dest, error_type: int, error_rate: float,
                     image: str = 'image/OIP.bmp', window_size: int = 10, timeout_interval: float = 0.05,
                     update_ui_callback = None):
        """
        Sends an image file over UDP using the Go-Back-N protocol.
        window_size: Number of packets to send before waiting for ACKs.
        timeout_interval: Fixed timeout for the oldest unacknowledged packet.
        """
        # Load image and serialize into bytes
        img = Image.open(image)
        numpydata = np.asarray(img)
        data_bytes = pickle.dumps(numpydata)

        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        # Create the list of packets
        packets = []
        for seq in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, seq)
            packets.append(packet)

        print(f"Sending {total_packets} packets using GBN with window size {window_size}...")

        base = 0
        next_seq_num = 0
        timer_start = None
        eg = error_gen.error_gen()

        retransmissions = 0
        duplicate_acks = 0
        total_acks_received = 0
        unique_acks_received = set()

        while base < total_packets:
            # Send packets within the window
            while next_seq_num < base + window_size and next_seq_num < total_packets:
                pkt = packets[next_seq_num]
                # Simulate data packet loss (Option 5)
                if error_type == 5 and random.random() < error_rate:
                    print(f">>> Simulating data packet loss for packet {next_seq_num}.")
                else:
                    pkt_to_send = pkt
                    # Simulate data packet bit-error (Option 3)
                    if error_type == 3:
                        pkt_to_send = eg.packet_error(pkt, error_rate)
                    port.sendto(pkt_to_send, dest)
                    print(f"Sent packet {next_seq_num}")
                # Start timer for the first unacknowledged packet
                if base == next_seq_num:
                    timer_start = time.time()
                next_seq_num += 1

            # Wait for ACK with timeout
            try:
                elapsed = time.time() - timer_start if timer_start is not None else 0
                remaining_time = timeout_interval - elapsed
                if remaining_time <= 0:
                    raise TimeoutError
                port.settimeout(remaining_time)
                ack_packet, _ = port.recvfrom(2)
                ack_num = struct.unpack("!H", ack_packet)[0]
                total_acks_received += 1
                if ack_num not in unique_acks_received:
                    unique_acks_received.add(ack_num)
                else:
                    duplicate_acks += 1
                print(f"Received ACK {ack_num}")

                # Slide window if ACK is valid
                if ack_num >= base:
                    base = ack_num + 1
                    # Restart timer if there are outstanding packets
                    if base < next_seq_num:
                        timer_start = time.time()
                    else:
                        timer_start = None

                    if update_ui_callback is not None:
                        progress = base / total_packets
                        update_ui_callback(progress, retransmissions, duplicate_acks)
            except Exception as e:
                # Timeout occurred; retransmit all packets in the current window
                print(f"Timeout occurred. Retransmitting packets from {base} to {next_seq_num - 1}.")
                for seq in range(base, next_seq_num):
                    pkt = packets[seq]
                    if error_type == 5 and random.random() < error_rate:
                        print(f">>> Simulating data packet loss for packet {seq} on retransmission.")
                    else:
                        pkt_to_send = pkt
                        if error_type == 3:
                            pkt_to_send = eg.packet_error(pkt, error_rate)
                        port.sendto(pkt_to_send, dest)
                        print(f"Retransmitted packet {seq}")
                retransmissions += (next_seq_num - base)
                timer_start = time.time()  # Restart timer

        # Send termination signal to indicate end of transmission
        port.sendto(b'END', dest)
        print("Image data sent successfully using GBN!")

        ack_efficiency = (len(unique_acks_received) / total_acks_received) * 100 if total_acks_received > 0 else 0
        print("\n===== Performance Metrics =====")
        print(f"Total ACKs Received: {total_acks_received}")
        print(f"Unique ACKs Received: {len(unique_acks_received)}")
        print(f"Retransmissions: {retransmissions}")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print("================================\n")

        return total_packets, retransmissions, duplicate_acks, ack_efficiency

    def update_progress(self, progress, retransmissions, duplicate_acks, ack_efficiency=0, retransmission_overhead=0):
        """Update UI dynamically."""
        self.progress_bar.set_value(progress)
        self.retrans_label.set_text(f"Retransmissions: {retransmissions}")
        self.dup_ack_label.set_text(f"Duplicate ACKs: {duplicate_acks}")
        self.ack_eff_label.set_text(f"ACK Efficiency: {ack_efficiency:.2f}")
        self.retrans_overhead_label.set_text(f"Retransmission Overhead: {retransmission_overhead:.2f}")
