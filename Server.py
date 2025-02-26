from socket import *
import receive
import send
import struct
from error_gen import error_gen


class Server:
    def main(self):
        serverPort = 12000
        serverSocket = socket(AF_INET, SOCK_DGRAM)

        # Initialize error generator
        error_simulator = error_gen()

        print(f"Starting server...")  # Debugging print
        serverSocket.bind(('', serverPort))
        print(f"Server is listening on port {serverPort}")

        while True:
            print("Waiting for client messages...")
            message, clientAddress = serverSocket.recvfrom(2048)
            message = message.decode()

            # Returns hello
            if message == 'HELLO':
                serverSocket.sendto(message.encode(), clientAddress)

            # Returns File to client
            elif message == 'GET':
                s = send.send()
                s.udp_send(serverSocket, clientAddress)

                #Sending ACK back to client
                ack_packet = struct.pack("!H", 0)  # ACK with sequence number 0
                ack_packet = error_simulator.packet_error(ack_packet, error_rate=0.2)
                serverSocket.sendto(ack_packet, clientAddress)

            # Receives file from client
            elif message == 'PUSH':
                r = receive.receive()
                r.udp_receive(serverSocket, True)

                # Sending another acknowledgment for PUSH
                ack_packet = struct.pack("!H", 1)  #ACK with sequence number 1
                ack_packet = error_simulator.packet_error(ack_packet, error_rate=0.2)
                serverSocket.sendto(ack_packet, clientAddress)

            # Ends communication
            elif message == 'END':
                break

        serverSocket.close()


if __name__ == '__main__':
    c = Server()
    c.main()
