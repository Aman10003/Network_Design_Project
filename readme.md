# Readme File
## Title and Authors
* Phase 2
* Anthony Mangino, Bryan Grullon, Nathan L, Yaritza Sanchez
## Environment
* Windows
* Python 3.13
* Packages
  * Numpy
  * Socket
  * PIL
  * Pickle
  * Random
  * struct
## Instructions
1. Start the server
   * Open a terminal or command prompt. 
   * Run the server 
     * python server.py
     * the server should display "Server is ready to receive connections" and listen for incoming connections from clients.

2. Start the Client 
   * Open another terminal or command prompt.
   * Run the client using the command:
     * python client.py

  The client should display a menu with options (H, G, P, E).

    Choose an option:
    
    H → Sends "Hello" to the server (server should respond).
    G → Requests an image from the server (image should transfer and be saved as client_image.bmp).
    P → Uploads an image to the server (user selects an image file to send).
    E → Ends the session and disconnects.

3. Running Image Transfers
Pushing an Image to the Server

   * Run the client and enter:
   * P
   * Choose an image file (ensure OIP.bmp is available in the directory).
   * The sender will divide the image into packets and transmit them.
   * The server will receive the packets, reassemble the image, and save it as server_image.bmp.
   * If successful, the client should print "Image sent successfully".

4. Retrieving an Image from the Server

   *   Run the client and enter:
   *   G
   *   The server will send the requested image in packets.
   *   The client will receive the image packets and save them as client_image.bmp.

  If successful, the client should print "Image received successfully".

* Code is developed in pycharm
* Must have all packages to run
  * Can use pip install in install any missing packages
  

## Files
* Client.py - Client-side implementation (sends commands to the server)
* Sever.py - Server-side implementation (handles client requests)
* send.py - Handles sending images using RDT 2.2 (sequence numbers, checksum, retransmission)
* receive.py - Handles receiving images using RDT 2.2 (sequence numbers, checksum verification
* OIP.bmp - original image  used for testing transmission
* client/server_image.bmp - Reconstructed image received after transmission.
* design.md - Documentation explaining file structure and implementation details.
* server_image.bmp - Reconstructed image received after transmission.
* error_gen.py - Generates errors for testing ACK and data corruption. Fixed timeout error.
* DEBUG.py - Debugging script. Fixed ACK issues
* .gitignore - Ignores unnecessary files in the repository. Updated for error_gen.py
