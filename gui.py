from nicegui import ui
import subprocess
import socket
import sys

# Label to display server response
response_label = ui.label('')

def run_server():
    python_executable = sys.executable  # Get the path to the current Python interpreter
    subprocess.Popen([python_executable, 'Server.py'])

def run_client_hello():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12000)
    message = 'HELLO'
    client_socket.sendto(message.encode(), server_address)
    server_message, _ = client_socket.recvfrom(2048)
    response_label.set_text(server_message.decode())  # Update label with server response
    client_socket.close()

def stop_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12000)
    message = 'END'
    client_socket.sendto(message.encode(), server_address)
    client_socket.close()

# Create buttons and label in the UI
with ui.row():
    ui.button('Start Server', on_click=run_server)
    ui.button('Send HELLO from Client', on_click=run_client_hello)
    response_label = ui.label('')
    ui.button('Stop Server', on_click=stop_server)

# Run the NiceGUI server
ui.run()