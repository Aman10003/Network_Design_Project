from socket import *
import pickle
import struct
import random
import time
from PIL import Image
import error_gen


class receive:
    def compute_parity(self, data):
        """Calculate a simple parity bit: 0 for even 1s, 1 for odd 1s."""
        ones_count = sum(bin(byte).count('1') for byte in data)
        return ones_count % 2  # Returns 0 or 1

    def udp_receive(self, port: socket, server: bool, error_type: int, error_rate: float):
        """Receives an image file over UDP using sequence numbers and checksum."""
        print('The server is ready to receive image data' if server else 'The client is ready to receive image data')

        received_data = {}
        expected_seq_num = 0  # Start with an initial expected sequence number

        # Initialized error_gen
        eg = error_gen.error_gen()

        while True:
            try:
                # Original Implementation
                # packet, address = port.recvfrom(4096 + 3)  # Sequence (2 bytes) + data + checksum (1 byte)

                port.setsockopt(SOL_SOCKET, SO_RCVBUF, 65536)  # Increase receive buffer

                # Second implementation to try and capture whole packet
                packet, address = port.recvfrom(65535)  # Sequence (2 bytes) + data + checksum (1 byte)
                # Check for termination signal
                if packet == b'END':
                    print("Received all packets, reconstructing the image...")
                    break

                # Ensure packet is large enough to contain a valid sequence number and checksum
                if len(packet) < 3:
                    print(">>> Received an incomplete packet! Ignoring...")
                    continue

                # Extract sequence number, data, and checksum safely
                seq_num = struct.unpack("!H", packet[:2])[0]
                data = packet[2:-1]  # Extract the actual image data
                received_checksum = packet[-1]

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

                # Update the expected sequence number for the next packet
                expected_seq_num += 1

                # Simulate network delay (0-500ms) before sending ACK
                delay = random.uniform(0, 0.5)
                time.sleep(delay)

                # Send ACK back to the sender
                ack_packet = struct.pack("!H", seq_num)
                # ACK packet error
                if error_type == 2:
                    ack_packet = eg.packet_error(ack_packet, error_rate)

                port.sendto(ack_packet, address)
                print(f"Sent ACK {seq_num}, Delay: {round(delay * 1000, 2)}ms")

            except Exception as e:
                print(f"Error receiving packet: {e}")

        # Reassemble the full image byte stream in order
        try:
            sorted_data = b''.join(received_data[i] for i in sorted(received_data.keys()))
            print(f"Total received data size: {len(sorted_data)} bytes")  # Debug print

            # Debugging code
            # # Save raw received data for inspection
            # with open("received_data.pkl", "wb") as f:
            #     f.write(sorted_data)
            #
            # print("Saved received data to 'received_data.pkl'. Try manually loading it with pickle.")

            # Deserialize the array
            numpydata = pickle.loads(sorted_data)  # <-- Error occurs here
            print("Deserialization successful.")

            # Convert array back to an image and save
            img = Image.fromarray(numpydata)
            if server:
                img.save("server_image.bmp")
            else:
                img.save("client_image.bmp")
            print("Image successfully saved as client/server_image.bmp")

        except pickle.UnpicklingError as e:
            print(f"Unpickling error: {e}")
        except Exception as e:
            print(f"Unexpected error during image reconstruction: {e}")
