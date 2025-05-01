# Client.py
from socket import *
import receive
import send
from tcp import TCPSender, TCPReceiver


class Client:
    def __init__(self):
        self.server_name = 'localhost'
        self.server_port = 12000
        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        self.error_type = 1
        self.error_rate = 0

    def error_selection(self):
        while True:
            try:
                self.error_type = int(input(
                    "Option 1 - No loss/bit-errors. Option 2 - ACK packet bit-error. Option 3 - Data packet bit-error. Option 4 - ACK packet loss. Option 5 - Data packet loss: "))
                if self.error_type in [1, 2, 3, 4, 5]:
                    break
                else:
                    print("Invalid option. Please enter 1, 2, 3, 4, or 5.")
            except ValueError:
                print("Invalid input. Please enter a number (1, 2, 3, 4, or 5).")
        if self.error_type != 1:
            while True:
                try:
                    self.error_rate = float(input("Select error rate (between 0 and 1): "))
                    if 0 <= self.error_rate < 1:
                        break
                    else:
                        print("Error rate must be between 0 and 1.")
                except ValueError:
                    print("Invalid input. Please enter a decimal number between 0 and 1.")
        else:
            self.error_rate = 0

    def say_hello(self):
        message = 'HELLO'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        server_message, _ = self.client_socket.recvfrom(2048)
        print(server_message.decode())

    def get_file(self):
        message = 'GET'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.error_selection()
        # Prompt for protocol selection.
        while True:
            protocol_choice = input(
                "Choose protocol for GET: 1 for Stop-and-Wait, 2 for GBN, 3 for Selective Repeat, 4 for TCP: "
            ).strip()
            if protocol_choice in ["1", "2", "3", "4"]:
                break
            else:
                print("Invalid protocol choice. Please enter 1, 2, 3 or 4.")
        protocol = {
            "1": "sw",
            "2": "gbn",
            "3": "sr",
            "4": "tcp"
        }[protocol_choice]

        message = str([self.error_type, self.error_rate, protocol])
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))

        # --- TCP branch ---
        if protocol == "tcp":

            # 1) 3-way handshake
            tcp = TCPSender(self.client_socket, (self.server_name, self.server_port))
            tcp.connect()

            # 2) receive file
            receiver = TCPReceiver(self.client_socket, (self.server_name, self.server_port))
            data = receiver.recv()

            with open("downloaded_file.bin", "wb") as f:
                    f.write(data)
            tcp.close()
            print("File received via TCP.")
            return

        r = receive.receive()
        r.udp_receive_protocol(self.client_socket, False, self.error_type, self.error_rate, protocol)

    def push_file(self):
        message = 'PUSH'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.error_selection()
        # Prompt for protocol selection.
        while True:
            protocol_choice = input(
                "Choose protocol for GET: 1 for Stop-and-Wait, 2 for GBN, 3 for Selective Repeat, 4 for TCP: "
            ).strip()
            if protocol_choice in ["1", "2", "3", "4"]:
                break
            else:
                print("Invalid protocol choice. Please enter 1, 2, 3 or 4.")

        protocol = {
            "1": "sw",
            "2": "gbn",
            "3": "sr",
            "4": "tcp"
        }[protocol_choice]

        message = str([self.error_type, self.error_rate, protocol])
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        file_loc = input("If you want a custom file, input file path now else press enter: ").strip()
        s = send.send()

        if protocol == "tcp":

            tcp = TCPSender(self.client_socket, (self.server_name, self.server_port))
            tcp.connect()

            with open(file_loc or "image/OIP.bmp", "rb") as f:
                data = f.read()
            tcp.send(data)
            tcp.close()
            print("File sent via TCP.")

            return

        # For protocols that use windowing, gather additional parameters.
        if protocol in ["gbn", "sr"]:
            while True:
                try:
                    window_size = int(input("Enter window size (e.g., 10): "))
                    if window_size > 0:
                        break
                    else:
                        print("Window size must be a positive integer.")
                except ValueError:
                    print("Invalid input. Please enter a valid integer for window size.")
            while True:
                try:
                    timeout_val = float(input("Enter timeout interval in seconds (e.g., 0.05): "))
                    if timeout_val > 0:
                        break
                    else:
                        print("Timeout must be a positive number.")
                except ValueError:
                    print("Invalid input. Please enter a valid number for timeout interval.")
            s.udp_send_protocol(self.client_socket,
                                (self.server_name, self.server_port),
                                self.error_type,
                                self.error_rate,
                                protocol=protocol,
                                image=(file_loc if file_loc != '' else 'image/OIP.bmp'),
                                window_size=window_size,
                                timeout_interval=timeout_val)
        else:
            s.udp_send_protocol(self.client_socket,
                                (self.server_name, self.server_port),
                                self.error_type,
                                self.error_rate,
                                protocol=protocol,
                                image=(file_loc if file_loc != '' else 'image/OIP.bmp'))

    def end_communication(self):
        message = 'END'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.client_socket.close()

    def main(self):
        while True:
            option = input('Select input of H (Hello), G (Get File), P (Push File), E (End):\n')
            if option.upper() == 'H':
                self.say_hello()
            elif option.upper() == 'G':
                self.get_file()
            elif option.upper() == 'P':
                self.push_file()
            elif option.upper() == 'E':
                self.end_communication()
                break
            else:
                print("Invalid option. Please enter H, G, P, or E.")

if __name__ == '__main__':
    c = Client()
    c.main()
