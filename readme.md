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
   -python server.py
2. Start the client
   -python client.py
3. The client should display a menu with options (H, G, P, E).
* Test sending basic commands:
  * H - Says hello to sever and sever responds
  * G - Gets image from server
  * P - Pushes image to server
    * Can select image location to push to sever
  * E - Ends the session
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
