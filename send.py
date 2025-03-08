from socket import *
import numpy as np
from PIL import Image
import pickle  # To serialize NumPy array
import struct  # To attach packet sequence numbers
import error_gen
import time
import checksums  # Import the checksums module

# # For debug
# import binascii

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

    def udp_send_with_progress(self, port: socket, dest, error_type: int, error_rate: float, update_ui_callback, image: str = 'image/OIP.bmp'):
        """Sends an image file over UDP with RDT 2.2, updating GUI progress."""
        # Load the image and convert it into a NumPy array
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Initialize error generator
        eg = error_gen.error_gen()

        # Define packet size
        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets...")

        port.settimeout(1.0)  # 1-second timeout for ACK reception

        # Increases sequence number for each packet
        sequence_number = 0
        MAX_RETRIES = 20

        retransmissions = 0  # Count packet retransmissions
        duplicate_acks = 0  # Count duplicate ACKs

        # Send packets
        for i in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, sequence_number)
            retries = 0

            while retries < MAX_RETRIES:
                try:
                    # Introduce packet errors if needed
                    packet_modified = packet
                    if error_type == 3:
                        packet_modified = eg.packet_error(packet, error_rate)

                    # Send packet
                    port.sendto(packet_modified, dest)
                    print(f"Sent packet {sequence_number}")

                    # Wait for ACK
                    ack_packet, _ = port.recvfrom(2)  # Expect a 2-byte ACK
                    ack_num = struct.unpack("!H", ack_packet)[0]

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received. Sending next packet.")
                        sequence_number += 1
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

            # Update UI progress
            progress = (sequence_number + 1) / total_packets
            update_ui_callback(progress, retransmissions, duplicate_acks)

        # Send termination signal
        port.sendto(b'END', dest)
        return total_packets, retransmissions, duplicate_acks
        print("Image data sent successfully!")
