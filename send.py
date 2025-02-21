from socket import *
import numpy as np
from PIL import Image
import pickle  # To serialize NumPy array
import struct  # To attach packet sequence numbers


class send:
    def make_packet(self, data_bytes, packet_size, sequence_number):
        """Creates a packet with a sequence number."""
        start = sequence_number * packet_size
        end = start + packet_size
        return struct.pack("!H", sequence_number) + data_bytes[start:end]

    def udp_send(self, port: socket, dest, image: str = 'image/OIP.bmp'):
        # Load the image and convert into numpy array
        img = Image.open(image)
        numpydata = np.asarray(img)

        # Serialize NumPy array
        data_bytes = pickle.dumps(numpydata)

        # Define packet size (UDP has a limit; we keep it smaller for safety)
        packet_size = 4096
        total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

        print(f"Sending {total_packets} packets...")

        # Send packets with sequence numbers
        for i in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, i)
            port.sendto(packet, dest)

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully!")
