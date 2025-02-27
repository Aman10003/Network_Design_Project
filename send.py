from socket import *
import numpy as np
from PIL import Image
import pickle  # To serialize NumPy array
import struct  # To attach packet sequence numbers
import error_gen


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

    def udp_send(self, port: socket, dest, error_type: int, error_rate: float, image: str = 'image/OIP.bmp'):
        """Sends an image file over UDP with RDT 2.2 (with sequence numbers, checksum, and delay)."""
        # Load the image and convert into numpy array
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Initialized error_gen
        eg = error_gen.error_gen()

        # Define packet size (UDP has a limit; we keep it smaller for safety)
        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets...")

        port.settimeout(1.0)  # 1 second timeout for ACK reception

        # Increases sequence number for each packet
        sequence_number = 0
        MAX_RETRIES = 5  # Define a retransmission limit

        # Send packets
        for i in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, sequence_number)
            retries = 0

            while retries < MAX_RETRIES:
                try:
                    # Error generation (if necessary)
                    if error_type == 3:
                        packet = eg.packet_error(packet, error_rate)

                    # Send packet
                    port.sendto(packet, dest)
                    print(f"Sent packet {sequence_number}")

                    # Wait for ACK
                    ack_packet, _ = port.recvfrom(2)  # Expect a 2-byte ACK
                    ack_num = struct.unpack("!H", ack_packet)[0]

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received. Sending next packet.")
                        sequence_number += 1
                        break  # Exit the retry loop
                    else:
                        print(f"Incorrect ACK {ack_num}. Retransmitting packet {sequence_number}...")
                except timeout:
                    retries += 1
                    print(f"Timeout for packet {sequence_number}. Retries: {retries}")

            if retries == MAX_RETRIES:
                print(f"Failed to send packet {sequence_number} after {MAX_RETRIES} retries.")
                return

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully!")
