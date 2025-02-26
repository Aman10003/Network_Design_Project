from socket import *
import pickle
import struct
from PIL import Image


class receive:
    def udp_receive(self, port: socket, server: bool):
        if server:
            print('The server is ready to receive image data')
        else:
            print('The server is ready to receive image data')

        received_data = {}
        expected_seq_num = 0  # Start with an initial expected sequence number

        while True:
            packet, address = port.recvfrom(4096 + 2)  # Packet + sequence number

            # Check for termination signal
            if packet == b'END':
                print("Received all packets, reconstructing the image...")
                break

            # Extract sequence number (first 2 bytes) and data
            seq_num = struct.unpack("!H", packet[:2])[0]
            data = packet[2:]

            if seq_num != expected_seq_num:  # Check for sequence number mismatch
                print(
                    f">>> Corrupted ACK or out-of-order packet! Expected {expected_seq_num}, but got {seq_num}. Retransmitting...")
                # Retransmit or log the error
                continue

            # Otherwise, we consider the packet valid.
            print(f"Received packet {seq_num}. Data added.")
            received_data[seq_num] = data  # Store packet by sequence number

            # Update the expected sequence number for the next packet
            expected_seq_num += 1

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
