from socket import *
import numpy as np
from PIL import Image
import pickle  # To serialize NumPy array
import struct  # To attach packet sequence numbers
import random
import error_gen
import time
import checksums  # Import the checksums module


class send:
    def __init__(self):
        self.progress_bar = None
        self.retrans_label = None
        self.dup_ack_label = None
        self.ack_eff_label = None
        self.retrans_overhead_label = None

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

    def adjust_packet_size(self, current_size, loss_rate, ack_delay):
        """Adjust packet size based on loss rate and ACK delay."""
        if loss_rate > 0.1 or ack_delay > 0.1:
            return max(1024, current_size // 2)  # Reduce packet size
        elif loss_rate < 0.01 and ack_delay < 0.05:
            return min(8192, current_size * 2)  # Increase packet size
        return current_size

    def load_image_bytes(self, image_path):
        img = Image.open(image_path)
        numpydata = np.asarray(img)
        return pickle.dumps(numpydata)

    def simulate_packet_error(self, packet, error_type, error_rate):

        print(f"Simulate_packet_error: Incoming packet type = {type(packet)}")  # NEW DEBUG PRINT

        if not isinstance(packet, (bytes, bytearray)):
            raise TypeError(f"Simulate_packet_error expects bytes! Got {type(packet)}")

        if error_type == 5 and random.random() < error_rate:
            return None  # Simulate drop
        elif error_type == 3:
            print(f"Packet type(sim error): {type(packet)}")  # Debug
            error_generator = error_gen.error_gen()  # <-- Create an instance
            packet = error_generator.packet_error(packet, error_rate)  # <-- Now call properly
            print(f"After packet_error, packet type: {type(packet)}")  # Debugging
            return packet

        return packet

    def calculate_total_packets(self, data_bytes, packet_size):
        return len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)

    def compute_metrics(self, total_packets, retransmissions, total_acks_received, unique_acks_received):
        ack_efficiency = (len(unique_acks_received) / total_acks_received) * 100 if total_acks_received else 0
        retrans_overhead = (retransmissions / total_packets) * 100
        return ack_efficiency, retrans_overhead

    def udp_send(self, port: socket, dest, error_type: int, error_rate: float, image: str = 'image/OIP.bmp',
                 update_ui_callback = None):
        """RDT 3.0 with adaptive timeout implementation."""

        data_bytes = self.load_image_bytes(image)

        packet_size = 4096
        total_packets = self.calculate_total_packets(data_bytes,packet_size)

        print(f"Sending {total_packets} packets using Stop-and-Wait (RDT 3.0)...")

        # Initial timeout values
        ERTT = 0.05  # Estimated RTT
        DevRTT = 0.01  # Deviation of RTT
        alpha = 0.125
        beta = 0.25

        sequence_number = 0
        MAX_RETRIES = 20

        retransmissions = 0  # Count packet retransmissions
        duplicate_acks = 0  # Count duplicate ACKs
        total_acks_received = 0  # Track total ACKs received
        unique_acks_received = set()  # Track unique ACKs received

        # Initialize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label,
             self.retrans_overhead_label] = update_ui_callback

        # Send initial packet with total_packets (2 bytes)
        init_packet = struct.pack("!H", total_packets)
        port.sendto(init_packet, dest)
        print(f"Sent total_packets info: {total_packets}")

        while sequence_number < total_packets:
            packet = self.make_packet(data_bytes, packet_size, sequence_number)
            # print(f"Constructed packet: {packet}")  # Debug
            print(f"Packet type: {type(packet)}")  # Debug
            retries = 0

            while retries < MAX_RETRIES:
                try:
                    # Introduce packet errors if needed

                    start_time = time.time()

                    pkt_to_send = self.simulate_packet_error(packet, error_type, error_rate)
                    print(f"Packet type(pkt_to_send): {type(pkt_to_send)}")  # Debug

                    # Ensure that the packet to send is not None or invalid
                    if pkt_to_send:
                        print(f"Sent packet {sequence_number}")
                        port.sendto(pkt_to_send, dest)
                    else:
                        print(f"Packet {sequence_number} was dropped due to error.")

                    # Adaptive timeout calculation
                    adaptive_timeout = max(0.05, min(ERTT + 4 * DevRTT, 0.5))  # between 50ms and 500ms
                    port.settimeout(adaptive_timeout)
                    print(f"Adaptive timeout is now {adaptive_timeout:.4f} seconds")

                    # Wait for ACK
                    ack_packet, _ = port.recvfrom(4) # 4 bytes: 2 for sequence number and 2 for checksum
                    end_time = time.time()

                    if len(ack_packet) != 4:
                        print("ACK packet size error!")
                        continue

                    # Extract the sequence number and its checksum
                    ack_seq = ack_packet[:2]
                    received_checksum = struct.unpack("!H", ack_packet[2:])[0]
                    computed_checksum = checksums.compute_checksum(ack_seq)

                    if received_checksum != computed_checksum:
                        print("ACK checksum error! Discarding ACK.")
                        continue

                    ack_num = struct.unpack("!H", ack_seq)[0]
                    total_acks_received += 1

                    if ack_num not in unique_acks_received:
                        unique_acks_received.add(ack_num)
                    else:
                        duplicate_acks += 1  # Count duplicate ACKs

                    if ack_num == sequence_number:
                        print(f"ACK {ack_num} received and verified. Sending next packet.")
                        sequence_number += 1  # Only increment on correct ACK

                        if update_ui_callback is not None:
                            progress = sequence_number / total_packets
                            self.update_progress(progress, retransmissions, duplicate_acks)

                        # Calculate RTT and update ERTT and DevRTT
                        RTT = end_time - start_time
                        print(f"Measured RTT: {RTT:.4f} seconds")
                        ERTT = (1 - alpha) * ERTT + alpha * RTT
                        DevRTT = (1 - beta) * DevRTT + beta * abs(RTT - ERTT)
                        print(f"Updated ERTT: {ERTT:.4f}, DevRTT: {DevRTT:.4f}")

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

        # Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully using RDT 3.0!")

        # Compute efficiency metrics
        ack_efficiency, retransmissions_overhead = self.compute_metrics(total_packets, retransmissions, total_acks_received, unique_acks_received)

        print("\n===== Performance Metrics =====")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print(f"Retransmission Overhead: {retransmissions_overhead:.2f}%")
        print("================================\n")

        return total_packets, retransmissions, duplicate_acks, ack_efficiency, retransmissions_overhead

    def udp_send_gbn(self, port: socket, dest, error_type: int, error_rate: float,
                     image: str = 'image/OIP.bmp', window_size: int = 10, timeout_interval: float = 0.05,
                     update_ui_callback = None):
        """
        Sends an image file over UDP using the Go-Back-N protocol.
        window_size: Number of packets to send before waiting for ACKs.
        timeout_interval: Fixed timeout for the oldest unacknowledged packet.
        """
        # Load image and serialize into bytes
        data_bytes = self.load_image_bytes(image)

        packet_size = 4096
        total_packets = self.calculate_total_packets(data_bytes,packet_size)

        # Create the list of packets
        packets = []
        for seq in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, seq)
            packets.append(packet)

        print(f"Sending {total_packets} packets using GBN with window size {window_size}...")

        base = 0
        next_seq_num = 0
        timer_start = None
        eg = error_gen.error_gen()

        retransmissions = 0
        duplicate_acks = 0
        total_acks_received = 0
        unique_acks_received = set()

        # Initialize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label,
             self.retrans_overhead_label] = update_ui_callback

        # Send initial packet with total_packets (2 bytes)
        init_packet = struct.pack("!H", total_packets)
        port.sendto(init_packet, dest)
        print(f"Sent total_packets info: {total_packets}")

        while base < total_packets:
            # Send packets within the window
            while next_seq_num < base + window_size and next_seq_num < total_packets:
                pkt = packets[next_seq_num]
                pkt_to_send = self.simulate_packet_error(pkt, error_type, error_rate)

                if pkt_to_send:
                    port.sendto(pkt_to_send, dest)
                    print(f"Sent packet {next_seq_num}")

                # Start timer for the first unacknowledged packet
                if base == next_seq_num:
                    timer_start = time.time()
                next_seq_num += 1

            # Wait for ACK with timeout
            try:
                elapsed = time.time() - timer_start if timer_start is not None else 0
                remaining_time = timeout_interval - elapsed
                if remaining_time <= 0:
                    raise TimeoutError
                port.settimeout(remaining_time)
                ack_packet, _ = port.recvfrom(4)

                if len(ack_packet) != 4:
                    print("ACK packet size error!")
                    continue

                ack_seq = ack_packet[:2]
                received_checksum = struct.unpack("!H", ack_packet[2:])[0]
                computed_checksum = checksums.compute_checksum(ack_seq)

                if update_ui_callback is not None:
                    progress = base / total_packets
                    self.update_progress(progress, retransmissions, duplicate_acks)

                if received_checksum != computed_checksum:
                    print("ACK checksum error! Discarding ACK.")
                    continue

                ack_num = struct.unpack("!H", ack_seq)[0]
                total_acks_received += 1
                if ack_num not in unique_acks_received:
                    unique_acks_received.add(ack_num)
                else:
                    duplicate_acks += 1
                print(f"Received ACK {ack_num}")
                print(f"Base before sliding: {base}")
                print(f"Base updated to: {base}")

                # Slide window if ACK is valid
                if ack_num >= base:
                    base = ack_num + 1
                    # Restart timer if there are outstanding packets
                    if base < next_seq_num:
                        timer_start = time.time()
                    else:
                        timer_start = None

                    if update_ui_callback is not None:
                        progress = base / total_packets
                        update_ui_callback(progress, retransmissions, duplicate_acks)
                # Continue sending in window
            except (timeout, TimeoutError):
                print(f"Timeout occurred. Retransmitting packets from {base} to {next_seq_num - 1}.")
                for seq in range(base, next_seq_num):
                    pkt = packets[seq]
                    if error_type == 5 and random.random() < error_rate:
                        print(f">>> Simulating data packet loss for packet {seq} on retransmission.")
                    else:
                        pkt_to_send = pkt
                        if error_type == 3:
                            pkt_to_send = eg.packet_error(pkt, error_rate)
                        port.sendto(pkt_to_send, dest)
                        print(f"Retransmitted packet {seq}")
                retransmissions += (next_seq_num - base)
                timer_start = time.time()  # Restart timer

        # Send termination signal to indicate end of transmission
        port.sendto(b'END', dest)
        print("Image data sent successfully using GBN!")

        ack_efficiency, retransmissions_overhead = self.compute_metrics(total_packets, retransmissions, total_acks_received, unique_acks_received)

        print("\n===== Performance Metrics =====")
        print(f"Total ACKs Received: {total_acks_received}")
        print(f"Unique ACKs Received: {len(unique_acks_received)}")
        print(f"Retransmissions: {retransmissions}")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print("================================\n")

        return total_packets, retransmissions, duplicate_acks, ack_efficiency, retransmissions_overhead

    def udp_send_sr(self, port: socket, dest, error_type: int, error_rate: float,
                    image: str = 'image/OIP.bmp', window_size: int = 10, timeout_interval: float = 0.05,
                    update_ui_callback=None):
        """
        Sends an image file over UDP using the Selective Repeat protocol.
        """
        # Load image
        data_bytes = self.load_image_bytes(image)

        packet_size = 4096
        total_packets = self.calculate_total_packets(data_bytes,packet_size)

        # Create packets with sequence numbers and checksums.
        packets = []
        for seq in range(total_packets):
            packet = self.make_packet(data_bytes, packet_size, seq)
            packets.append(packet)

        print(f"Sending {total_packets} packets using Selective Repeat with window size {window_size}...")

        base = 0
        next_seq = 0
        window = {}  # {seq: {"packet": packet, "acked": False, "timer": timestamp}}

        retransmissions = 0
        duplicate_acks = 0
        total_acks_received = 0
        unique_acks_received = set()
        eg = error_gen.error_gen()

        # Initialize ui_update values
        if update_ui_callback is not None:
            [self.progress_bar, self.retrans_label, self.dup_ack_label, self.ack_eff_label,
             self.retrans_overhead_label] = update_ui_callback

        # Send initial packet with total_packets (2 bytes)
        init_packet = struct.pack("!H", total_packets)
        port.sendto(init_packet, dest)
        print(f"Sent total_packets info: {total_packets}")

        while base < total_packets:
            # Fill the window: send packets not yet sent.
            while next_seq < total_packets and next_seq < base + window_size:
                if next_seq not in window:
                    window[next_seq] = {"packet": packets[next_seq], "acked": False, "timer": time.time()}
                    packet = window[next_seq]["packet"]
                    pkt_to_send = self.simulate_packet_error(packet, error_type, error_rate)

                    if pkt_to_send:
                        port.sendto(pkt_to_send, dest)
                        print(f"Sent packet {next_seq} (Selective Repeat)")
                next_seq += 1

            # Listen for ACKs using a short timeout.
            try:
                port.settimeout(0.01)
                ack_packet, _ = port.recvfrom(4)
                if len(ack_packet) != 4:
                    continue
                ack_seq = struct.unpack("!H", ack_packet[:2])[0]
                received_checksum = struct.unpack("!H", ack_packet[2:])[0]
                computed_checksum = checksums.compute_checksum(ack_packet[:2])
                if received_checksum != computed_checksum:
                    print("ACK checksum error! Discarding ACK.")
                    continue
                total_acks_received += 1
                if update_ui_callback is not None:
                    progress = ack_seq / total_packets
                    self.update_progress(progress, retransmissions, duplicate_acks)
                if ack_seq not in unique_acks_received:
                    unique_acks_received.add(ack_seq)
                else:
                    duplicate_acks += 1
                print(f"Received ACK {ack_seq} (Selective Repeat)")
                if ack_seq in window:
                    window[ack_seq]["acked"] = True
            except timeout:
                pass

            # Check for packets in the window whose timers have expired.
            current_time = time.time()
            for seq in list(window.keys()):
                if not window[seq]["acked"] and (current_time - window[seq]["timer"]) > timeout_interval:
                    pkt = window[seq]["packet"]
                    if error_type == 5 and random.random() < error_rate:
                        print(f">>> Simulating data packet loss for retransmitted packet {seq}.")
                    else:
                        pkt_to_send = pkt
                        if error_type == 3:
                            pkt_to_send = eg.packet_error(pkt, error_rate)
                        port.sendto(pkt_to_send, dest)
                        print(f"Retransmitted packet {seq} (Selective Repeat)")
                    retransmissions += 1
                    window[seq]["timer"] = current_time

            # Slide the window by removing consecutively acknowledged packets.
            while base in window and window[base]["acked"]:
                del window[base]
                base += 1

        # Send termination signal.
        port.sendto(b'END', dest)
        print("Image data sent successfully using Selective Repeat!")
        ack_efficiency, retransmissions_overhead = self.compute_metrics(total_packets, retransmissions, total_acks_received, unique_acks_received)

        print("\n===== Performance Metrics (Selective Repeat) =====")
        print(f"Total ACKs Received: {total_acks_received}")
        print(f"Unique ACKs Received: {len(unique_acks_received)}")
        print(f"Retransmissions: {retransmissions}")
        print(f"ACK Efficiency: {ack_efficiency:.2f}%")
        print("==================================================\n")

        return total_packets, retransmissions, duplicate_acks, ack_efficiency, retransmissions_overhead

    def udp_send_protocol(self, port: socket, dest, error_type: int, error_rate: float,
                          protocol: str = "sw", image: str = 'image/OIP.bmp',
                          window_size: int = 10, timeout_interval: float = 0.05,
                          update_ui_callback=None):
        """
        Unified function to send data using a selectable protocol.
        protocol: "sw" for Stop-and-Wait, "gbn" for Go-Back-N, "sr" for Selective Repeat.
        """
        protocol = protocol.lower()
        if protocol == "gbn":
            return self.udp_send_gbn(port, dest, error_type, error_rate, image, window_size, timeout_interval, update_ui_callback)
        elif protocol == "sr":
            return self.udp_send_sr(port, dest, error_type, error_rate, image, window_size, timeout_interval, update_ui_callback)
        else:
            return self.udp_send(port, dest, error_type, error_rate, image, update_ui_callback)

    def update_progress(self, progress, retransmissions, duplicate_acks, ack_efficiency=0, retransmission_overhead=0):
        """Update UI dynamically."""
        self.progress_bar.set_value(progress)
        self.retrans_label.set_text(f"Retransmissions: {retransmissions}")
        self.dup_ack_label.set_text(f"Duplicate ACKs: {duplicate_acks}")
        self.ack_eff_label.set_text(f"ACK Efficiency: {ack_efficiency:.2f} %")
        self.retrans_overhead_label.set_text(f"Retransmission Overhead: {retransmission_overhead:.2f} %")
