from socket import *
import receive
import send


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
        message = str([self.error_type, self.error_rate])
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        r = receive.receive()
        r.udp_receive(self.client_socket, False, self.error_type, self.error_rate)

    def push_file(self):
        message = 'PUSH'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.error_selection()
        # Prompt for protocol selection.
        while True:
            protocol_choice = input(
                "Choose protocol: 1 for RDT 3.0 (Stop-and-Wait), 2 for GBN, 3 for Selective Repeat: ").strip()
            if protocol_choice in ["1", "2", "3"]:
                break
            else:
                print("Invalid protocol choice. Please enter 1, 2, or 3.")
        # Send error parameters along with the protocol selection.
        message = str([self.error_type, self.error_rate, protocol_choice])
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        file_loc = input("If you want a custom file, input now else press enter: ").strip()
        s = send.send()

        if protocol_choice == "2":
            # Validate parameters for GBN.
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
            s.udp_send_gbn(self.client_socket,
                           (self.server_name, self.server_port),
                           self.error_type,
                           self.error_rate,
                           file_loc if file_loc != '' else 'image/OIP.bmp',
                           window_size,
                           timeout_val)
        elif protocol_choice == "3":
            # Validate parameters for Selective Repeat.
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
            s.udp_send_sr(self.client_socket,
                          (self.server_name, self.server_port),
                          self.error_type,
                          self.error_rate,
                          file_loc if file_loc != '' else 'image/OIP.bmp',
                          window_size,
                          timeout_val)
        else:
            # Stop-and-Wait (RDT 3.0)
            s.udp_send(self.client_socket,
                       (self.server_name, self.server_port),
                       self.error_type,
                       self.error_rate,
                       file_loc if file_loc != '' else 'image/OIP.bmp')

    def end_communication(self):
        message = 'END'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.client_socket.close()

    def main(self):
        while True:
            option = input('Select input of H (Hello), G (Get File), P (Push File), E (End):\n')
            if option == 'H':
                self.say_hello()
            elif option == 'G':
                self.get_file()
            elif option == 'P':
                self.push_file()
            elif option == 'E':
                self.end_communication()
                break
            else:
                print("Invalid option. Please enter H, G, P, or E.")

if __name__ == '__main__':
    c = Client()
    c.main()
