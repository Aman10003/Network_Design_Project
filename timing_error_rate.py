import csv
import time
from socket import *
import send

def run_test(error_rate):
    server_name = 'localhost'
    server_port = 12000
    client_socket = socket(AF_INET, SOCK_DGRAM)

    # Send PUSH request
    client_socket.sendto(b'PUSH', (server_name, server_port))
    client_socket.sendto(str([5, error_rate]).encode(), (server_name, server_port))  # Error type 5 = Data Loss

    s = send.send()

    start_time = time.time()
    total_packets, retransmissions, duplicate_acks, ack_efficiency, retrans_overhead = s.udp_send_gbn(
        client_socket,
        (server_name, server_port),
        5,  # error_type
        error_rate,
        window_size=10,
        timeout_interval=0.05  # For now, fixed timeout; later we can sweep this
    )
    end_time = time.time()
    time_taken = end_time - start_time

    total_bytes = total_packets * 4096
    throughput = total_bytes / time_taken if time_taken > 0 else 0

    client_socket.close()

    return [error_rate, time_taken, throughput, retransmissions, ack_efficiency, retrans_overhead]


def main():
    with open('chart1_error_rate.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Error Rate", "Completion Time (s)", "Throughput (bytes/s)", "Retransmissions", "ACK Efficiency (%)", "Retransmission Overhead (%)"])

        for i in range(13):  # 0.0 to 0.6
            error_rate = round(i * 0.05, 2)
            result = run_test(error_rate)
            writer.writerow(result)
            print(f"Done: Error Rate {error_rate}")

if __name__ == '__main__':
    main()
