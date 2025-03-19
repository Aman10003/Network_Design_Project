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

    # For gui implementations
    def udp_send_with_progress(self, port: socket, dest, error_type: int, error_rate: float, update_ui_callback,
                               image: str = 'image/OIP.bmp'):
        """Sends an image file over UDP with RDT 2.2, updating GUI progress."""
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Initialize error generator
        eg = error_gen.error_gen()

        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets...")

        port.settimeout(0.05)  # 50ms timeout for ACK reception

        sequence_number = 0
        MAX_RETRIES = 20

        retransmissions = 0  # Count packet retransmissions
        duplicate_acks = 0  # Count duplicate ACKs

        while sequence_number < total_packets:
            packet = self.make_packet(data_bytes, packet_size, sequence_number)
            retries = 0

            while retries < MAX_RETRIES:
                try:
                    # Introduce packet errors if needed
                    packet_modified = packet
                    if error_type == 3:
                        packet_modified = eg.packet_error(packet, error_rate)

                    # Simulate data packet loss
                    if error_type == 5 and random.random() < error_rate:
                        print(f">>> Simulating data packet loss for packet {sequence_number}.")
                    else:
                        # Send packet
                        port.sendto(packet_modified, dest)
                        print(f"Sent packet {sequence_number}")

                    # Wait for ACK
                    ack_packet, _ = port.recvfrom(2)  # Expect a 2-byte ACK
                    ack_num = struct.unpack("!H", ack_packet)[0]

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received. Sending next packet.")
                        sequence_number += 1  # Only increment on correct ACK

                        # Update UI progress **only after successful transmission**
                        progress = sequence_number / total_packets
                        update_ui_callback(progress, retransmissions, duplicate_acks)

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
        print("Image data sent successfully!")

        return total_packets, retransmissions, duplicate_acks

    # For non gui_implementation
    def adjust_packet_size(self, current_size, loss_rate, ack_delay):
        """Adjust packet size based on loss rate and ACK delay."""
        if loss_rate > 0.1 or ack_delay > 0.1:
            return max(1024, current_size // 2)  # Reduce packet size
        elif loss_rate < 0.01 and ack_delay < 0.05:
            return min(8192, current_size * 2)  # Increase packet size
        return current_size

    def udp_send(self, port: socket, dest, error_type: int, error_rate: float, image: str = 'image/OIP.bmp'):
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

        retransmissions = 0  # Count packet retransmissions
        duplicate_acks = 0  # Count duplicate ACKs

        while sequence_number < total_packets:
            packet = self.make_packet(data_bytes, packet_size, sequence_number)
            retries = 0

            while retries < MAX_RETRIES:
                try:
                    # Introduce packet errors if needed
                    packet_modified = packet
                    if error_type == 3:
                        packet_modified = eg.packet_error(packet, error_rate)

                    # Send packet
                    start_time = time.time()
                    port.sendto(packet_modified, dest)
                    print(f"Sent packet {sequence_number}")

                    # Wait for ACK
                    port.settimeout(ERTT + 4 * DevRTT)  # Adaptive timeout
                    ack_packet, _ = port.recvfrom(2)  # 2-byte ACK
                    end_time = time.time()

                    ack_num = struct.unpack("!H", ack_packet)[0]

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received. Sending next packet.")
                        sequence_number += 1  # Only increment on correct ACK

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
        print("Image data sent successfully!")

        return total_packets, retransmissions, duplicate_acks