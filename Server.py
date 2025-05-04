from socket import *
import receive
import send
import ast  # To safely convert string representation of a list back to a list
import json
from tcp import TCPSender, TCPReceiver


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
                # Only decode if it's a control message, not TCP data
                try:
                    decoded_message = message.decode()
                    print(f"Received message: {decoded_message} from {clientAddress}")
                    message = decoded_message  # Use the decoded message for further processing
                except UnicodeDecodeError:
                    # This is likely binary data (TCP segment), don't try to decode
                    print(f"Received binary data from {clientAddress}")
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
                    # Try to parse the message as JSON
                    try:
                        received_list = json.loads(decoded_message)  # Parse JSON data
                        error_type = received_list[0]
                        error_rate = received_list[1]
                        protocol = received_list[2] if len(received_list) > 2 else "gbn"  # Default protocol
                    except json.JSONDecodeError:
                        # Handle the case where the message is not valid JSON
                        print(f"Received invalid parameters: {decoded_message}")
                        raise ValueError(f"Invalid parameters format: {decoded_message}")
                    print(f"Received error_type: {error_type}, error_rate: {error_rate}, protocol: {protocol}")

                    if protocol == "tcp":

                        # passive open → handshake
                        receiver = TCPReceiver(serverSocket, clientAddress)
                        receiver.listen()

                        # load file and send
                        with open("image/OIP.bmp", "rb") as f:
                            file_data = f.read()
                        sender = TCPSender(serverSocket, clientAddress)
                        try:
                            sender.send(file_data)
                            sender.close()
                            print("Served GET via TCP.")
                        except Exception as e:
                            print(f"Error in TCP send: {e}")
                            # Try to close the connection gracefully
                            try:
                                sender.close()
                            except:
                                pass

                    else:
                        s = send.send()
                        s.udp_send_protocol(serverSocket, clientAddress,
                                                error_type, error_rate,
                                                protocol = protocol,
                                                window_size = 10,
                                                timeout_interval = 0.05)

                except Exception as e:
                    print(f"Error while handling 'GET' request: {e}")


            elif message == 'PUSH':
                print("Received 'PUSH' request from client.")
                try:
                    error_message, clientAddress = serverSocket.recvfrom(1024)  # Buffer size of 1024 bytes
                    decoded_message = error_message.decode()
                    try:
                        received_list = json.loads(decoded_message)  # Parse JSON data
                        error_type = received_list[0]
                        error_rate = received_list[1]
                        protocol = received_list[2] if len(received_list) > 2 else "gbn"
                    except json.JSONDecodeError:
                        # Handle the case where the message is not valid JSON
                        print(f"Received invalid parameters: {decoded_message}")
                        raise ValueError(f"Invalid parameters format: {decoded_message}")
                    print(f"Received error_type: {error_type}, error_rate: {error_rate}, protocol: {protocol}")

                    if protocol == "tcp":

                        receiver = TCPReceiver(serverSocket, clientAddress)
                        if receiver.listen():  # Check if handshake was successful
                            data = receiver.recv()

                            with open("uploaded_file.bmp", "wb") as f:
                                # Check if data starts with "M" but missing "B"
                                if data.startswith(b"M") and not data.startswith(b"BM"):
                                    # Prepend the missing "B"
                                    data = b"B" + data
                                # Keep the existing code for finding BMP header elsewhere
                                elif not data.startswith(b"BM"):
                                    bmp_header_pos = data.find(b"BM")
                                    if bmp_header_pos > 0:
                                       data = data[bmp_header_pos:]

                                f.write(data)
                            print(f"Received PUSH via TCP ({len(data)} bytes).")
                    else:
                        r = receive.receive()
                        r.udp_receive_protocol(serverSocket, True,
                                                        error_type, error_rate,
                                                        protocol = protocol,
                                                        window_size = 10)

                except Exception as e:

                    print(f"Error while handling 'PUSH' request: {e}")


            elif message == 'END':
                print("Ending communication, closing server.")
                serverSocket.close()
                break


if __name__ == '__main__':
    c = Server()
    c.main()
