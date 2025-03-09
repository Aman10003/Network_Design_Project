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

        while True:
            serverSocket.settimeout(50)  # Timeout after 50 seconds
            print("Waiting for client messages...")
            try:
                message, clientAddress = serverSocket.recvfrom(2048)
                message = message.decode()
                print(f"Received message: {message} from {clientAddress}")  # Debugging message
            except timeout:
                print("No message received, continuing...")
                continue  # Go back to waiting for a new message

            if message == "HELLO":
                print("Responding to 'HELLO' from client...")
                serverSocket.sendto("Hello from server!".encode(), clientAddress)  # Respond with a custom message

            elif message == 'GET':
                print("Received 'GET' request from client.")
                # Waiting for error type and error rate (assuming this is part of the GET request)
                try:
                    error_message, clientAddress = serverSocket.recvfrom(1024)  # Buffer size of 1024 bytes
                    decoded_message = error_message.decode()
                    received_list = ast.literal_eval(decoded_message)  # Safely parse the list
                    error_type = received_list[0]
                    error_rate = received_list[1]
                    print(f"Received error_type: {error_type}, error_rate: {error_rate}")  # Debugging print

                    # Send data based on error type and rate
                    s = send.send()
                    s.udp_send(serverSocket, clientAddress, error_type, error_rate)
                except Exception as e:
                    print(f"Error while handling 'GET' request: {e}")

            elif message == 'PUSH':
                print("Received 'PUSH' request from client.")
                try:
                    error_message, clientAddress = serverSocket.recvfrom(1024)  # Buffer size of 1024 bytes
                    decoded_message = error_message.decode()
                    received_list = ast.literal_eval(decoded_message)  # Safely parse the list
                    error_type = received_list[0]
                    error_rate = received_list[1]
                    print(f"Received error_type: {error_type}, error_rate: {error_rate}")  # Debugging print

                    # Receive data based on error type and rate
                    r = receive.receive()
                    r.udp_receive(serverSocket, True, error_type, error_rate)
                except Exception as e:
                    print(f"Error while handling 'PUSH' request: {e}")

            elif message == 'END':
                print("Ending communication, closing server.")
                serverSocket.close()
                break

if __name__ == '__main__':
    c = Server()
    c.main()