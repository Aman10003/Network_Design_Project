import csv
import time
from socket import *
import receive
import send


class Client:
    def error_selection(self, error_rate):
        self.error_type = 2  # For ACK packet bit-error
        self.error_rate = error_rate

    def main(self):
        serverName = 'localhost'
        serverPort = 12000
        clientSocket = socket(AF_INET, SOCK_DGRAM)

        # Open CSV file to store results
        with open('push_results.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Error Rate", "Time Taken (s)"])

            # Loop through error rates from 0% to 60% in 5% increments
            for error_rate in [i * 0.05 for i in range(13)]:
                self.error_selection(error_rate)

                # Measure the time for the PUSH operation
                start_time = time.time()

                # PUSH operation
                message = 'PUSH'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                message = str([self.error_type, self.error_rate])
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                s = send.send()

                s.udp_send(clientSocket, (serverName, serverPort), self.error_type, self.error_rate)

                # Calculate the time taken
                end_time = time.time()
                time_taken = end_time - start_time

                # Write the error rate and time taken to the CSV file
                writer.writerow([self.error_rate * 100, time_taken])

                print(f"PUSH with {self.error_rate * 100}% error rate completed in {time_taken:.4f} seconds.")

        clientSocket.close()


if __name__ == '__main__':
    c = Client()
    c.main()
