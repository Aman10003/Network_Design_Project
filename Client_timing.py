import csv
import time
from socket import *
import receive
import send

class Client:
    def error_selection(self, error_type, error_rate):
        self.error_type = error_type
        self.error_rate = error_rate

    def main(self):
        serverName = 'localhost'
        serverPort = 12000
        clientSocket = socket(AF_INET, SOCK_DGRAM)

        # Open CSV file to store results
        with open('performance_results.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Error Type", "Error Rate", "Completion Time (s)", "Throughput (bytes/s)"])

            # Loop through error types 1 to 5
            for error_type in range(1, 6):
                # Loop through error rates from 0% to 60% in 5% increments
                for error_rate in [i * 0.05 for i in range(13)]:
                    self.error_selection(error_type, error_rate)

                    # Measure the time for the PUSH operation
                    start_time = time.time()

                    # PUSH operation
                    message = 'PUSH'
                    clientSocket.sendto(message.encode(), (serverName, serverPort))
                    message = str([self.error_type, self.error_rate])
                    clientSocket.sendto(message.encode(), (serverName, serverPort))
                    s = send.send()

                    total_packets, retransmissions, duplicate_acks = s.udp_send(clientSocket, (serverName, serverPort), self.error_type, self.error_rate)

                    # Calculate the time taken
                    end_time = time.time()
                    time_taken = end_time - start_time

                    # Calculate throughput (bytes/s)
                    total_bytes = total_packets * 4096  # Packet size 4096 bytes
                    throughput = total_bytes / time_taken if time_taken > 0 else 0

                    # Write the error type, error rate, time taken, and throughput to the CSV file
                    writer.writerow([self.error_type, self.error_rate * 100, time_taken, throughput])

                    print(f"PUSH with Error Type {self.error_type} and {self.error_rate * 100}% error rate completed in {time_taken:.4f} seconds with throughput {throughput:.2f} bytes/s.")

        clientSocket.close()

if __name__ == '__main__':
    c = Client()
    c.main()