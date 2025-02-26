from socket import *
import pickle
import struct
import random
import time
from PIL import Image


class receive:
    def compute_parity(self, data):
        """Calculate a simple parity bit: 0 for even 1s, 1 for odd 1s."""
        ones_count = sum(bin(byte).count('1') for byte in data)
        return ones_count % 2  # Returns 0 or 1

    def udp_receive(self, port: socket, server: bool):
        """Receives an image file over UDP using sequence numbers and checksum."""
        print('The server is ready to receive image data' if server else 'The client is ready to receive image data')

        received_data = {}
        expected_seq_num = 0  # Start with an initial expected sequence number

        while True:
            packet, address = port.recvfrom(4096 + 3)  # Sequence (2 bytes) + data + checksum (1 byte)

            # Check for termination signal
            if packet == b'END':
                print("Received all packets, reconstructing the image...")
                break

            # Extract sequence number, data, and checksum
            seq_num, data, received_checksum = struct.unpack("!H4096sB", packet)
            computed_checksum = self.compute_parity(data)  # Compute checksum from data

            if received_checksum != computed_checksum:
                print(f">>> Checksum error in packet {seq_num}! Expected {computed_checksum}, got {received_checksum}.")
                continue  # Ignore corrupted packet

            if seq_num != expected_seq_num:  # Check for sequence number mismatch
                print(f">>> Out-of-order packet! Expected {expected_seq_num}, but got {seq_num}. Ignoring...")
                continue

            # Otherwise, packet is valid.
            print(f"Received packet {seq_num}. Checksum verified. Data added.")
            received_data[seq_num] = data  # Store packet by sequence number

            # Update the expected sequence number for the next packet (Alternating Bit Protocol)
            expected_seq_num = 1 - expected_seq_num

            # Simulate network delay (0-500ms) before sending ACK
            delay = random.uniform(0, 0.5)
            time.sleep(delay)

            # Send ACK back to the sender
            ack_packet = struct.pack("!H", seq_num)
            port.sendto(ack_packet, address)
            print(f"Sent ACK {seq_num}, Delay: {round(delay * 1000, 2)}ms")

        # Reassemble the full image byte stream in order
        sorted_data = b''.join(received_data[i] for i in sorted(received_data.keys()))

        # Deserialize the array
        numpydata = pickle.loads(sorted_data)

        # Convert array back to an image and save
        img = Image.fromarray(numpydata)
        img.save("server_image.bmp" if server else "client_image.bmp")
        print("Image successfully saved as server_image.bmp or client_image.bmp")
