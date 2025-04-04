import csv
import time
from socket import *
import send

def run_test(error_rate, use_gbn=True):
    server_name = 'localhost'
    server_port = 12000
    client_socket = socket(AF_INET, SOCK_DGRAM)

    print(f"\n[RUNNING] Error Rate = {error_rate:.2f} | Protocol = {'GBN' if use_gbn else 'RDT 3.0'}")

    try:
        client_socket.sendto(b'PUSH', (server_name, server_port))
        client_socket.sendto(str([5, error_rate]).encode(), (server_name, server_port))

        s = send.send()
        start_time = time.time()

        if use_gbn:
            total_packets, retransmissions, duplicate_acks, ack_efficiency = s.udp_send_gbn(
                client_socket,
                (server_name, server_port),
                5,
                error_rate,
                timeout_interval=0.05,
                window_size=10
            )
            retrans_overhead = (retransmissions / total_packets) * 100 if total_packets > 0 else 0
        else:
            total_packets, retransmissions, duplicate_acks, ack_efficiency, retrans_overhead = s.udp_send(
                client_socket,
                (server_name, server_port),
                5,
                error_rate,
                fixed_timeout=0.1
            )

        end_time = time.time()
        time_taken = end_time - start_time
        total_bytes = total_packets * 4096
        throughput = total_bytes / time_taken if time_taken > 0 else 0

        client_socket.close()
        return [error_rate, time_taken, throughput, retransmissions, ack_efficiency, retrans_overhead]

    except Exception as e:
        print(f"[ERROR] Error rate {error_rate} → {e}")
        client_socket.close()
        return [error_rate, 0, 0, 0, 0, 0]

def main():
    with open('chart1_error_rate.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Error Rate",
            "Completion Time (s)",
            "Throughput (bytes/s)",
            "Retransmissions",
            "ACK Efficiency (%)",
            "Retransmission Overhead (%)"
        ])

        for i in range(13):  # 0.0 to 0.6 in 0.05 steps
            error_rate = round(i * 0.05, 2)
            result = run_test(error_rate, use_gbn=True)
            writer.writerow(result)

if __name__ == '__main__':
    main()
