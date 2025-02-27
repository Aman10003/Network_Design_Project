from socket import *
import receive
import send
import ast  # To safely convert string representation of a list back to a list


class Server:
    def main(self):
        serverPort = 12000
        serverSocket = socket(AF_INET, SOCK_DGRAM)

        print(f"Starting server...")  # Debugging print
        serverSocket.bind(('', serverPort))
        print(f"Server is listening on port {serverPort}")
        serverSocket.settimeout(500)  # Timeout after 500 seconds

        while True:
            print("Waiting for client messages...")
            try:
                message, clientAddress = serverSocket.recvfrom(2048)
                message = message.decode()
            except timeout:
                print("No message received, continuing...")
                continue  # Go back to waiting for a new message

            if message == "PUSH" or message == "GET":
                # Assuming you have a UDP socket set up as `serverSocket`
                error_message, clientAddress = serverSocket.recvfrom(1024)  # Buffer size of 1024 bytes

                # Decode and convert the message back to a list
                decoded_message = error_message.decode()
                received_list = ast.literal_eval(decoded_message)  # Safely parse the list

                # Extract values
                error_type = received_list[0]
                error_rate = received_list[1]

            # Returns hello
            if message == 'HELLO':
                serverSocket.sendto(message.encode(), clientAddress)

            # Returns File to client
            elif message == 'GET':
                s = send.send()
                s.udp_send(serverSocket, clientAddress, error_type, error_rate)

            # Receives file from client
            elif message == 'PUSH':
                r = receive.receive()
                r.udp_receive(serverSocket, True, error_type, error_rate)

            # Ends communication
            elif message == 'END':
                print("Ending communication, closing server.")
                serverSocket.close()
                break



if __name__ == '__main__':
    c = Server()
    c.main()
