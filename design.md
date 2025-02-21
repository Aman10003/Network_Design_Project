
# Design File
## Title and Authors
* Phase 1
* Anthony Mangino
## Purpose of The Phase
Code Explanation

The code is split up into 4 main files
* Server
* Client
* Send
* Receive

### Client and Sever setup
The client and sever have very similar code. 
They both start with the import of necessary code
>from socket import *
> 
>import receive
>
>import send

This imports socket and receive/send functions

Then the sockets are set up
* Client
> serverName = 'localhost'
> 
> serverPort = 12000
> 
> clientSocket = socket(AF_INET, SOCK_DGRAM)

* Server
> serverPort = 12000
> 
> clientSocket = socket(AF_INET, SOCK_DGRAM)
> 
> serverSocket.bind(('', serverPort))

Both client and server enters a while True loop than runs until a break
### Client
The client then chooses which option to go with based on user input
* Asks user
> option = input('Select input of H, G, P, E\n')
* H / Hello
> #### Says hello to sever and waits for response
    if option == 'H':
        message = 'HELLO'
        clientSocket.sendto(message.encode(), (serverName, serverPort))
        serverMessage, serverAddress = clientSocket.recvfrom(2048)
        print(serverMessage.decode())

* G / Get

Calls receive.py
> #### Gets file from sever
    elif option == "G":
        message = 'GET'
        clientSocket.sendto(message.encode(), (serverName, serverPort))
        r = receive.receive()
        r.udp_receive(clientSocket, False)

* P / Push

Calls send.py
> #### Pushes file to sever and will either uses default image or image based on address given
    elif option == 'P':
        message = 'PUSH'
        clientSocket.sendto(message.encode(), (serverName, serverPort))
        file_loc = input("If you want custom file, input now else press enter")
        s = send.send()
        if file_loc.strip() == '':
            s.udp_send(clientSocket, (serverName, serverPort))
        else:
            s.udp_send(clientSocket, (serverName, serverPort), file_loc)

* E / End
>#### Ends communication
    elif option == 'E':
        message = 'END'
        clientSocket.sendto(message.encode(), (serverName, serverPort))
        break

### Sever
First the sever waits for client to tell it which mode it wants
>message, clientAddress = serverSocket.recvfrom(2048)
>
>message = message.decode()

* Hello
> #### Returns hello
    if message == 'HELLO':
        serverSocket.sendto(message.encode(), clientAddress)

* Get

Calls send.py
> #### Returns File to client
    elif message == 'GET':
        s = send.send()
        s.udp_send(serverSocket, clientAddress)

* Push

Calls receive.py
> #### Receives file from client
    elif message == 'PUSH':
        r = receive.receive()
        r.udp_receive(serverSocket, True)

* End
> #### Ends communication
    elif message == 'END':
        break

Both client and server close out using
> socketName.close()

### How packets are sent
First all packages are imported 
>from socket import *
>
> import numpy as np
> 
> from PIL import Image
> 
> import pickle  # To serialize NumPy array
> 
> import struct  # To attach packet sequence numbers

Parameters for both send and receive sockets as well as image source are then passed from client or server
>udp_send(self, port: socket, dest, image: str = 'image/OIP.bmp')

Then the image is imported and processed
> #### Load the image and convert into numpy array
    img = Image.open(image)
    numpydata = np.asarray(img)
> #### Serialize NumPy array
    data_bytes = pickle.dumps(numpydata)

Packet parameters are defined and then user is informed of total packets
> packet_size = 4096 
> 
> total_packets = len(data_bytes) // packet_size + (1 if len(data_bytes) % packet_size else 0)
>
> print(f"Sending {total_packets} packets...")


> #### Send packets with sequence numbers
    for i in range(total_packets):
        packet = self.make_packet(data_bytes, packet_size, i)
        port.sendto(packet, dest)

> #### Send termination signal
        port.sendto(b'END', dest)
        print("Image data sent successfully!")

#### How packets are made
    def make_packet(self, data_bytes, packet_size, sequence_number):  
    	"""Creates a packet with a sequence number."""  
        start = sequence_number * packet_size  
        end = start + packet_size  
        return struct.pack("!H", sequence_number) + data_bytes[start:end]

### How packets are received
The same packages are imported as the send file except we don't use numpy in this one

#### Function Definition
only need receiving socket and whether it's the server or the client
    
    def udp_receive(self, port: socket, sever: bool):

User is informed that client or server is ready to receive and an array is created

    if server:
        print('The server is ready to receive image data')
    else:
        print('The server is ready to receive image data')
        
    received_data = {}

Then we enter a while True loop to receive the packets until end signal is receive
    
    packet, address = port.recvfrom(4096 + 2)  # Packet + sequence number

    # Check for termination signal
    if packet == b'END':
        print("Received all packets, reconstructing the image...")
        break

    # Extract sequence number (first 2 bytes) and data
    seq_num = struct.unpack("!H", packet[:2])[0]
    data = packet[2:]

    received_data[seq_num] = data  # Store packet by sequence number

> #### Reassemble the full image byte stream in order
        sorted_data = b''.join(received_data[i] for i in sorted(received_data.keys()))

> #### Deserialize the array
        numpydata = pickle.loads(sorted_data)

Finally, image is converted back and then saved

    img = Image.fromarray(numpydata)
    if server:
        img.save("server_image.bmp")
    else:
        img.save("client_image.bmp")
    print("Image successfully saved as client/server_image.bmp")






