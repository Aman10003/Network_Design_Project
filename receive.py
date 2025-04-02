from socket import *
import pickle
import struct
import random
import time
from PIL import Image
import error_gen
import checksums  # Import the checksums module

class receive:
    def __init__(self):
        """Initialize tracking variables to avoid AttributeError."""
        self.total_acks_sent = 0  # Ensure this variable is initialized
        self.unique_acks_sent = set()  # Also initialize unique ACK tracking

    def ack_packet(self, index, port, address):
        # Simulate network delay (0-500ms) before sending ACK
        delay = random.uniform(0, 0.5)
        time.sleep(delay)

        ack_packet = struct.pack("!H", index)  # Last valid packet
        port.sendto(ack_packet, address)

        #Ensure variables exist before modifying them
        if not hasattr(self, 'total_acks_sent'):
            self.total_acks_sent = 0
        if not hasattr(self, 'unique_acks_sent'):
            self.unique_acks_sent = set()

        # Track ACK statistics
        self.total_acks_sent += 1
        self.unique_acks_sent.add(index)
        print(f"Sent ACK {index}, Delay: {round(delay * 1000, 2)}ms")

    def udp_receive(self, port: socket, server: bool, error_type: int, error_rate: float, window_size: int = 10):
        """Receives an image file over UDP using Go-Back-N protocol."""
        print('The server is ready to receive image data' if server else 'The client is ready to receive image data')

        received_data = {}
        expected_seq_num = 0  # Start with an initial expected sequence number

        # Initialized error_gen
        eg = error_gen.error_gen()
        port.setsockopt(SOL_SOCKET, SO_RCVBUF, 65536)  # Increase receive buffer

        while True:
            try:
                packet, address = port.recvfrom(65535)

                # Check for termination signal
                if packet == b'END':
                    print("Received all packets, reconstructing the image...")
                    break

                # Ensure packet is large enough to contain a valid sequence number and checksum
                if len(packet) < 4:
                    print(">>> Received an incomplete packet! Ignoring...")
                    continue

                # Extract sequence number, data, and checksum safely
                seq_num = struct.unpack("!H", packet[:2])[0]  # Unpack 2-byte sequence number
                data = packet[2:-2]  # Extract the actual image data (excluding the last 2 bytes)
                received_checksum = struct.unpack("!H", packet[-2:])[0]  # Unpack the last 2 bytes as checksum

                computed_checksum = checksums.compute_checksum(data)  # Compute checksum from data
                print(f"Receiver computed checksum: {computed_checksum}, Received checksum: {received_checksum}")

                # Handle checksum error
                if received_checksum != computed_checksum:
                    print(f">>> Checksum error in packet {seq_num}! Discarding...")
                    continue

                # Handle out-of-order packets
                if seq_num != expected_seq_num:
                    print(f">>> Out-of-order packet! Expected {expected_seq_num}, got {seq_num}. Ignoring...")
                    # Resend the last ACK to indicate the expected sequence number
                    if expected_seq_num > 0:
                        self.ack_packet(expected_seq_num - 1, port, address)
                    continue

                # Otherwise, packet is valid.
                print(f"Received packet {seq_num}. Checksum verified. Data added.")
                received_data[seq_num] = data  # Store packet by sequence number

                # Update the expected sequence number for the next packet
                expected_seq_num += 1

                # Send cumulative ACK for the last correctly received packet
                ack_packet = struct.pack("!H", expected_seq_num - 1)

                # Simulate ACK packet loss
                if error_type == 4 and random.random() < error_rate:
                    print(f">>> Simulating ACK packet loss for ACK {expected_seq_num - 1}.")
                    continue

                port.sendto(ack_packet, address)
                print(f"Sent ACK {expected_seq_num - 1}")

            except Exception as e:
                print(f"Error receiving packet: {e}")

        # Reassemble the full image byte stream in order
        sorted_data = b''.join(received_data[i] for i in sorted(received_data.keys()))
        numpydata = pickle.loads(sorted_data)

        # Convert array back to an image and save
        img = Image.fromarray(numpydata)
        if server:
            img.save("server_image.bmp")
        else:
            img.save("client_image.bmp")
        print("Image successfully saved as client/server_image.bmp")