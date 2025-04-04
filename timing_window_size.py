import csv
import time
from socket import *
import send

def run_test(window_size):
    server_name = 'localhost'
    server_port = 12000
    client_socket = socket(AF_INET, SOCK_DGRAM)

    # Send PUSH request
    client_socket.sendto(b'PUSH', (server_name, server_port))
    client_socket.sendto(str([5, 0.2]).encode(), (server_name, server_port))  # Error type 5 = Data Loss

    s = send.send()

    start_time = time.time()
    total_packets, retransmissions, duplicate_acks, ack_efficiency, retrans_overhead = s.udp_send_gbn(
        client_socket,
        (server_name, server_port),
        5,             # error_type
        0.2,           # error_rate
        timeout_interval=0.05,
        window_size=window_size
    )
    end_time = time.time()

    time_taken = end_time - start_time
    total_bytes = total_packets * 4096
    throughput = total_bytes / time_taken if time_taken > 0 else 0

    client_socket.close()

    return [window_size, time_taken, throughput, retransmissions, ack_efficiency, retrans_overhead]

def main():
    with open('chart3_window_size.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Window Size", "Completion Time (s)", "Throughput (bytes/s)", "Retransmissions", "ACK Efficiency (%)", "Retransmission Overhead (%)"])

        for size in [1, 2, 5, 10, 20, 50, 100]:
            result = run_test(size)
            writer.writerow(result)
            print(f"Done: Window Size {size}")

if __name__ == '__main__':
    main()
