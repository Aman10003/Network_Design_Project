from socket import *
import numpy as np
from PIL import Image
import pickle  # To serialize NumPy array
import struct  # To attach packet sequence numbers
import time  # To introduce random delays
import random  # For network delay simulation


class send:
    def compute_parity(self, data):
        """Calculate a simple parity bit: 0 for even 1s, 1 for odd 1s."""
        ones_count = sum(bin(byte).count('1') for byte in data)
        return ones_count % 2  # Returns 0 or 1

    def make_packet(self, data_bytes, packet_size, sequence_number):
        """Creates a packet with sequence number and checksum."""
        start = sequence_number * packet_size
        end = start + packet_size
        chunk = data_bytes[start:end]

        # Compute parity bit
        parity_bit = self.compute_parity(chunk)

        # Attach sequence number (2 bytes) + chunk + checksum (1 byte)
        return struct.pack("!H", sequence_number) + chunk + struct.pack("!B", parity_bit)

    def udp_send(self, port: socket, dest, image: str = 'image/OIP.bmp'):
        """Sends an image file over UDP with RDT 2.2 (with sequence numbers, checksum, and delay)."""
        # Load the image and convert into numpy array
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Define packet size (UDP has a limit; we keep it smaller for safety)
        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets...")

        # Alternating sequence number (0 or 1)
        sequence_number = 0

        # Send packets with sequence numbers
        for i in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, sequence_number)

            # Introduce a random network delay (0-500ms)
            delay = random.uniform(0, 0.5)
            time.sleep(delay)

            # Send packet
            port.sendto(packet, dest)
            print(f"Sent packet {sequence_number}, Checksum: {packet[-1]}, Delay: {round(delay*1000, 2)}ms")

            # Wait for ACK
            ack_packet, _ = port.recvfrom(2)
            ack_num = struct.unpack("!H", ack_packet)[0]

            if ack_num == sequence_number:
                print(f"ACK {ack_num} received. Sending next packet.")
                # Toggle sequence number between 0 and 1
                sequence_number = 1 - sequence_number
            else:
                print(f"ACK {ack_num} incorrect! Retransmitting packet {sequence_number}...")

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully!")
