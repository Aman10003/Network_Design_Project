from socket import *
import receive
import send

class Server:
    def main(self):
        serverPort = 12000
        serverSocket = socket(AF_INET, SOCK_DGRAM)
        serverSocket.bind(('', serverPort))

        while True:
            message, clientAddress = serverSocket.recvfrom(2048)
            message = message.decode()
            # Returns hello
            if message == 'HELLO':
                serverSocket.sendto(message.encode(), clientAddress)
            # Returns File to client
            elif message == 'GET':
                s = send.send()
                s.udp_send(serverSocket, clientAddress)
            # Receives file from client
            elif message == 'PUSH':
                r = receive.receive()
                r.udp_receive(serverSocket, True)
            # Ends communication
            elif message == 'END':
                break
        serverSocket.close()


if __name__ == '__main__':
    c = Server()
    c.main()
