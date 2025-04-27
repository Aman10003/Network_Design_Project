from socket import *
import pickle
import struct
import random
import time
from PIL import Image
from error_gen import error_gen
import checksums  # Import the checksums module


class receive:
    def __init__(self):
        """Initialize tracking variables to avoid AttributeError."""
        self.retrans_overhead_label = None
        self.ack_eff_label = None
        self.dup_ack_label = None
        self.retrans_label = None
        self.progress_bar = None
        self.total_acks_sent = 0  # Ensure this variable is initialized
        self.unique_acks_sent = set()  # Also initialize unique ACK tracking

    def ack_packet(self, index, port, address, error_type: int = 1, error_rate: float = 0):
        # Simulate network delay (0-100ms) before sending ACK
        delay = random.uniform(0, 0.1)
        time.sleep(delay)

        # Pack the sequence number into 2 bytes
        ack_seq = struct.pack("!H", index)

        # Compute checksum on the sequence number bytes
        ack_checksum = checksums.compute_checksum(ack_seq)

        # Append the checksum (2 bytes) to the ACK packet
        ack_packet = ack_seq + struct.pack("!H", ack_checksum)

        eg = error_gen()

        if error_type == 4 and random.random() < error_rate:
            ack_packet = None
        elif error_type == 2:
            ack_packet = eg.packet_error(ack_packet, error_rate)

        # Send the 4-byte ACK packet
        port.sendto(ack_packet, address)

        # Ensure variables exist before modifying them
        # if not hasattr(self, 'total_acks_sent'):
        #     self.total_acks_sent = 0
        # if not hasattr(self, 'unique_acks_sent'):
        #     self.unique_acks_sent = set()

        # Track ACK statistics
        self.total_acks_sent += 1
        self.unique_acks_sent.add(index)
        print(f"Sent ACK {index} with checksum {ack_checksum}, Delay: {round(delay * 1000, 2)}ms")

    def udp_receive(self, port: socket, server: bool, error_type: int, error_rate: float, use_gbn=False, update_ui_callback = None):
        """Receives an image file over UDP using sequence numbers and checksum."""
        mode = "GBN" if use_gbn else "Stop-and-Wait"
        print('The server is ready to receive image data' if server else 'The client is ready to receive image data')
        print(f"Receiver running in {mode} mode")

        received_data = {}
        expected_seq_num = 0
        retransmissions = 0
        duplicate_acks = 0


        port.setsockopt(SOL_SOCKET, SO_RCVBUF, 65536)  # Increase receive buffer

        # Initialize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label,
             self.retrans_overhead_label] = update_ui_callback

        # Receive total packet count from sender
        try:
            meta_packet, _ = port.recvfrom(1024)
            expected_total_packets = struct.unpack("!H", meta_packet[:2])[0]
            print(f"[Control] Expected total packets to receive: {expected_total_packets}")
        except Exception as e:
            print(f"Error receiving metadata: {e}")
            return

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

                # Extract sequence number, data, and checksum from the packet
                seq_num = struct.unpack("!H", packet[:2])[0]
                data = packet[2:-2]
                received_checksum = struct.unpack("!H", packet[-2:])[0]

                # Compute checksum over the data (as done on the sender side)
                computed_checksum = checksums.compute_checksum(data)
                print(f"Receiver computed checksum: {computed_checksum}, Received checksum: {received_checksum}")

                # If checksum fails, discard packet and resend ACK for last valid packet
                if received_checksum != computed_checksum:
                    print(f">>> Checksum error in packet {seq_num}! Discarding...")
                    # Resend the last ACK for the previous packet
                    if expected_seq_num > 0:
                        self.ack_packet(expected_seq_num - 1, port, address, error_type, error_rate)
                        retransmissions += 1
                        print(f"Resent ACK {expected_seq_num - 1} due to checksum error.")
                    continue

                # Check for out-of-order packet (applies to both GBN and Stop-and-Wait)
                if seq_num != expected_seq_num:
                    print(f">>> Out-of-order packet! Expected {expected_seq_num}, got {seq_num}. Ignoring...")
                    ack_num = max(0, expected_seq_num - 1)
                    self.ack_packet(ack_num, port, address, error_type, error_rate)
                    duplicate_acks += 1
                    continue

                # Otherwise, packet is valid.
                print(f"Received packet {seq_num}. Checksum verified. Data added.")
                received_data[seq_num] = data  # Store packet by sequence number

                # Update the expected sequence number for the next packet
                expected_seq_num += 1

                # Simulate network delay (0-100ms) before sending ACK
                delay = random.uniform(0, 0.1)
                time.sleep(delay)

                # Send ACK for the packet just received using the dedicated method
                self.ack_packet(seq_num, port, address, error_type, error_rate)

                if self.progress_bar:
                    progress = (len(received_data) / expected_total_packets) * 100
                    ack_eff = (len(self.unique_acks_sent) / self.total_acks_sent) * 100 if self.total_acks_sent > 0 else 0
                    overhead = ((self.total_acks_sent - len(self.unique_acks_sent)) / self.total_acks_sent) * 100 if self.total_acks_sent > 0 else 0
                    self.update_progress(progress, retransmissions, duplicate_acks, ack_eff, overhead)

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

            # Compute and display ACK Efficiency
            ack_efficiency = (len(self.unique_acks_sent) / self.total_acks_sent) * 100 if self.total_acks_sent > 0 else 0
            print("\n===== Performance Metrics =====")
            print(f"Total ACKs Sent: {self.total_acks_sent}")
            print(f"Unique ACKs Sent: {len(self.unique_acks_sent)}")
            print(f"ACK Efficiency: {ack_efficiency:.2f}%")
            print("================================\n")

    def udp_receive_sr(self, port: socket, server: bool, error_type: int, error_rate: float, window_size: int = 10, update_ui_callback = None):
        """
        Receives an image file over UDP using the Selective Repeat protocol.
        """

        print('The server is ready to receive image data' if server else 'The client is ready to receive image data')
        print("Receiver running in Selective Repeat mode")

        received_data = {}  # Buffer to store packets by sequence number
        expected_seq = 0
        retransmissions = 0
        duplicate_acks = 0

        port.setsockopt(SOL_SOCKET, SO_RCVBUF, 65536)

        # Initialize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label,
             self.retrans_overhead_label] = update_ui_callback

        # Receive total packet count from sender
        try:
            meta_packet, _ = port.recvfrom(1024)
            expected_total_packets = struct.unpack("!H", meta_packet[:2])[0]
            print(f"[Control] Expected total packets to receive: {expected_total_packets}")
        except Exception as e:
            print(f"Error receiving metadata: {e}")
            return

        while True:
            try:
                packet, address = port.recvfrom(65535)
                if packet == b'END':
                    print("Received termination signal. Reassembling image...")
                    break

                if len(packet) < 4:
                    print("Incomplete packet received. Ignoring.")
                    continue

                seq_num = struct.unpack("!H", packet[:2])[0]
                data = packet[2:-2]
                received_checksum = struct.unpack("!H", packet[-2:])[0]
                computed_checksum = checksums.compute_checksum(data)
                print(f"Receiver computed checksum: {computed_checksum}, Received checksum: {received_checksum}")

                if received_checksum != computed_checksum:
                    print(f"Checksum error in packet {seq_num}. Discarding.")
                    retransmissions += 1
                    continue

                # Accept packet if within the receiver's window.
                if seq_num < expected_seq or seq_num >= expected_seq + window_size:
                    print(f"Packet {seq_num} is outside the receiving window. Sending ACK anyway.")
                    self.ack_packet(seq_num, port, address, error_type, error_rate)
                    duplicate_acks += 1
                    continue

                # Buffer the packet and send an ACK.
                received_data[seq_num] = data
                self.ack_packet(seq_num, port, address, error_type, error_rate)
                print(f"Accepted packet {seq_num} and sent ACK.")

                # Slide the window if the expected packet(s) have arrived.
                while expected_seq in received_data:
                    expected_seq += 1

                if self.progress_bar:
                    progress = (len(received_data) / expected_total_packets) * 100
                    ack_eff = (len(self.unique_acks_sent) / self.total_acks_sent) * 100 if self.total_acks_sent > 0 else 0
                    overhead = ((self.total_acks_sent - len(self.unique_acks_sent)) / self.total_acks_sent) * 100 if self.total_acks_sent > 0 else 0
                    self.update_progress(progress, retransmissions, duplicate_acks, ack_eff, overhead)

            except Exception as e:
                print(f"Error receiving packet: {e}")
                break

        # Reassemble and reconstruct the image.
        try:
            sorted_data = b''.join(received_data[i] for i in sorted(received_data.keys()))
            print(f"Total received data size: {len(sorted_data)} bytes")
            numpydata = pickle.loads(sorted_data)
            print("Deserialization successful.")
            img = Image.fromarray(numpydata)
            if server:
                img.save("server_image_sr.bmp")
            else:
                img.save("client_image_sr.bmp")
            print("Image successfully saved as server_image_sr.bmp or client_image_sr.bmp")
        except Exception as e:
            print(f"Error reconstructing image: {e}")

    def udp_receive_protocol(self, port: socket, server: bool, error_type: int, error_rate: float,
                               protocol: str = "sw", window_size: int = 10):
        """
        Unified function to receive data using a selectable protocol.
        protocol: "sw" for Stop-and-Wait, "gbn" for Go-Back-N, "sr" for Selective Repeat.
        """
        protocol = protocol.lower()
        if protocol == "gbn":
            return self.udp_receive(port, server, error_type, error_rate, use_gbn=True)
        elif protocol == "sr":
            return self.udp_receive_sr(port, server, error_type, error_rate, window_size)
        else:
            return self.udp_receive(port, server, error_type, error_rate, use_gbn=False)
        
    
    def update_progress(self, progress, retransmissions, duplicate_acks, ack_efficiency=0, retransmission_overhead=0):
        """Update UI dynamically."""
        self.progress_bar.set_value(progress)
        self.retrans_label.set_text(f"Retransmissions: {retransmissions}")
        self.dup_ack_label.set_text(f"Duplicate ACKs: {duplicate_acks}")
        self.ack_eff_label.set_text(f"ACK Efficiency: {ack_efficiency:.2f} %")
        self.retrans_overhead_label.set_text(f"Retransmission Overhead: {retransmission_overhead:.2f} %")

