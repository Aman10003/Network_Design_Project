import csv
import time
from socket import *
import send

def run_test(fixed_timeout, use_gbn=True):
    server_name = 'localhost'
    server_port = 12000
    client_socket = socket(AF_INET, SOCK_DGRAM)

    print(f"\n[RUNNING] Timeout = {fixed_timeout:.2f}s | Protocol = {'GBN' if use_gbn else 'RDT 3.0'}")

    try:
        # Send PUSH request
        client_socket.sendto(b'PUSH', (server_name, server_port))
        client_socket.sendto(str([5, 0.2]).encode(), (server_name, server_port))  # Error type 5 = Data Loss

        s = send.send()
        start_time = time.time()

        if use_gbn:
            total_packets, retransmissions, duplicate_acks, ack_efficiency = s.udp_send_gbn(
                client_socket,
                (server_name, server_port),
                5,
                0.2,
                timeout_interval=fixed_timeout,
                window_size=10
            )
            retrans_overhead = (retransmissions / total_packets) * 100 if total_packets > 0 else 0
        else:
            total_packets, retransmissions, duplicate_acks, ack_efficiency, retrans_overhead = s.udp_send(
                client_socket,
                (server_name, server_port),
                5,
                0.2,
                fixed_timeout=fixed_timeout
            )

        end_time = time.time()
        time_taken = end_time - start_time
        total_bytes = total_packets * 4096
        throughput = total_bytes / time_taken if time_taken > 0 else 0

        print(f"[SUCCESS] Time = {time_taken:.3f}s | Throughput = {throughput:.2f} Bps | Retrans = {retransmissions}")

        client_socket.close()
        return [fixed_timeout, time_taken, throughput, retransmissions, ack_efficiency, retrans_overhead]

    except Exception as e:
        print(f"[ERROR] Test failed for timeout {fixed_timeout}s → {e}")
        client_socket.close()
        return [fixed_timeout, 0, 0, 0, 0, 0]

def main():
    with open('chart2_timeout.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timeout (s)",
            "Completion Time (s)",
            "Throughput (bytes/s)",
            "Retransmissions",
            "ACK Efficiency (%)",
            "Retransmission Overhead (%)"
        ])

        for timeout in [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]:
            result = run_test(timeout, use_gbn=True)  # Change to False to test RDT 3.0
            writer.writerow(result)

if __name__ == '__main__':
    main()
