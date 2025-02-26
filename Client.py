from socket import *
import receive
import send


class Client:

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
                r = receive.receive()
                r.udp_receive(clientSocket, False)
            # Pushes file to sever
            elif option == 'P':
                message = 'PUSH'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                file_loc = input("If you want custom file, input now else press enter")
                s = send.send()
                if file_loc.strip() == '':
                    s.udp_send(clientSocket, (serverName, serverPort))
                else:
                    s.udp_send(clientSocket, (serverName, serverPort), file_loc)
            # Ends communication
            elif option == 'E':
                message = 'END'
                clientSocket.sendto(message.encode(), (serverName, serverPort))
                break

        clientSocket.close()


if __name__ == '__main__':
    c = Client()
    c.main()