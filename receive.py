from socket import *
import pickle
import struct
import random
import time
from PIL import Image
import error_gen
import checksums  # Import the checksums module

class receive:
    def ack_packet(self, index, port, address):
        # Simulate network delay (0-500ms) before sending ACK
        delay = random.uniform(0, 0.5)
        time.sleep(delay)

        ack_packet = struct.pack("!H", index)  # Last valid packet
        port.sendto(ack_packet, address)

    def udp_receive(self, port: socket, server: bool, error_type: int, error_rate: float):
        """Receives an image file over UDP using sequence numbers and checksum."""
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
                    # Resend the last ACK for the previous packet
                    if expected_seq_num > 0:
                        self.ack_packet(expected_seq_num - 1, port, address)
                        print(f"Resent ACK {expected_seq_num - 1} due to checksum error.")
                    continue

                # Handle out-of-order packets
                if seq_num != expected_seq_num:
                    print(f">>> Out-of-order packet! Expected {expected_seq_num}, got {seq_num}. Ignoring...")
                    # Resend the last ACK to indicate the expected sequence number
                    if expected_seq_num > 0:
                        self.ack_packet(expected_seq_num - 1, port, address)
                        print(f"Resent ACK {expected_seq_num - 1} due to out-of-order packet.")
                    continue

                # Simulate data packet loss
                if error_type == 4 and random.random() < error_rate:
                    print(f">>> Simulating data packet loss for packet {seq_num}.")
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

            # Deserialize the array
            numpydata = pickle.loads(sorted_data)
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