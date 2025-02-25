from socket import *
import pickle
import struct
from PIL import Image


class receive:
    def udp_receive(self, port: socket, server: bool):
        print('The server is ready to receive image data' if server else 'Client ready to receive image data')
        received_data = {}

        while True:
            packet, address = port.recvfrom(4096 + 3)  # Packet + sequence number

            # Check for termination signal
            if packet == b'END':
                print("Received all packets, reconstructing the image...")
                break

            # Extract sequence number (first 2 bytes) and data
            seq_num = struct.unpack("!H", packet[:2])[0]
            received_parity = struct.unpack("!B", packet[2:3])[0]
            data = packet[3:]

            calculated_parity = self.calculate_parity(data)

            if received_parity == calculated_parity:
                print(f"Received valid packet {seq_num} with correct parity {received_parity}")
                received_data[seq_num] = data # Store packet by sequence number
            else:
                print(f"Parity mismatch for packet {seq_num}, expected {calculated_parity} but got {received_parity}")

        # Reassemble the full image byte stream in order
        sorted_data = b''.join(received_data[i] for i in sorted(received_data.keys()))

        # Deserialize the array
        numpydata = pickle.loads(sorted_data)

        # Convert array back to an image and save
        img = Image.fromarray(numpydata)
        if server:
            img.save("server_image.bmp")
        else:
            img.save("client_image.bmp")
        print("Image successfully saved as client/server_image.bmp")
        
        def calculate_parity(self, data_bytes):
        count_ones = sum(bin(byte).count('1') for byte in data_bytes)
        return count_ones % 2
