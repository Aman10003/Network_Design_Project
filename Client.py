from socket import *
import receive
import send


class Client:

    def error_selection(self):
        while True:
            try:
                self.error_type = int(input(
                    "Option 1 - No loss/bit-errors. Option 2 - ACK packet bit-error. Option 3 - Data packet bit-error: "))
                if self.error_type in [1, 2, 3]:
                    break
                else:
                    print("Invalid option. Please enter 1, 2, or 3.")
            except ValueError:
                print("Invalid input. Please enter a number (1, 2, or 3).")


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

    def main(self):
        serverName = 'localhost'
        serverPort = 12000
        clientSocket = socket(AF_INET, SOCK_DGRAM)

        while True:
            # Select option
            option = input('Select input of H, G, P, E\n')
            # Says hello to sever
            if option == 'H':
                message = 'HELLO'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                serverMessage, serverAddress = clientSocket.recvfrom(2048)
                print(serverMessage.decode())
            # Gets file from sever
            elif option == "G":
                message = 'GET'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                self.error_selection()
                message = str([self.error_type, self.error_rate])
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                r = receive.receive()
                r.udp_receive(clientSocket, False, self.error_type, self.error_rate)
            # Pushes file to sever
            elif option == 'P':
                message = 'PUSH'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                self.error_selection()
                message = str([self.error_type, self.error_rate])
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                file_loc = input("If you want custom file, input now else press enter")
                s = send.send()
                if file_loc.strip() == '':
                    s.udp_send(clientSocket, (serverName, serverPort), self.error_type, self.error_rate)
                else:
                    s.udp_send(clientSocket, (serverName, serverPort), self.error_type, self.error_rate, file_loc)
            # Ends communication
            elif option == 'E':
                message = 'END'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                break

        clientSocket.close()


if __name__ == '__main__':
    c = Client()
    c.main()
