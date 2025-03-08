from nicegui import ui
import subprocess
import socket
import sys

# Display server responses
response_textbox = ui.textarea(label='Server Responses')

def run_server():
    python_executable = sys.executable  # Get the path to the current Python interpreter
    subprocess.Popen([python_executable, 'Server.py'])

def run_client_hello():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12000)
    message = 'HELLO'
    client_socket.sendto(message.encode(), server_address)
    server_message, _ = client_socket.recvfrom(2048)
    response_textbox.value += f'HELLO Response: {server_message.decode()}\n'  # Append server response to text box
    client_socket.close()

def run_client_get(error_rate):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12000)
    message = 'GET'
    client_socket.sendto(message.encode(), server_address)
    error_message = str([1, error_rate])  # Assuming error_type 1 for GET
    client_socket.sendto(error_message.encode(), server_address)
    server_message, _ = client_socket.recvfrom(2048)
    response_textbox.value += f'GET Response: {server_message.decode()}\n'  # Append server response to text box
    client_socket.close()

def run_client_push(error_rate):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12000)
    message = 'PUSH'
    client_socket.sendto(message.encode(), server_address)
    error_message = str([2, error_rate])  # Assuming error_type 2 for PUSH
    client_socket.sendto(error_message.encode(), server_address)
    server_message, _ = client_socket.recvfrom(2048)
    response_textbox.value += f'PUSH Response: {server_message.decode()}\n'  # Append server response to text box
    client_socket.close()

def stop_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12000)
    message = 'END'
    client_socket.sendto(message.encode(), server_address)
    response_textbox.value += 'Server stopped.\n'  # Append server stop message to text box
    client_socket.close()

# Manage the visibility of the error rate controls
class ErrorRate:
    def __init__(self):
        self.visible = False
        self.error_rate = 0.0

error_rate = ErrorRate()

# Create UI elements
def create_ui():
    with ui.row():
        ui.button('Start Server', on_click=run_server)
        ui.button('Send HELLO from Client', on_click=run_client_hello)
        ui.button('Stop Server', on_click=stop_server)

    with ui.row():
        get_button = ui.button('Get')
        push_button = ui.button('Push')

    # Create a label and slider for selecting error rate (only visible when Get or Push)
    with ui.column().bind_visibility_from(error_rate, 'visible'):
        error_rate_label = ui.label('Select Error Rate')
        error_rate_slider = ui.slider(min=0, max=1, step=0.01).bind_value(error_rate, 'error_rate')
        error_rate_value = ui.label().bind_text_from(error_rate, 'error_rate')

    # Show error rate controls when Get or Push button is clicked
    def show_error_rate_controls():
        error_rate.visible = True

    get_button.on('click', show_error_rate_controls)
    push_button.on('click', show_error_rate_controls)

    # Create a button to execute the Get option
    def execute_get():
        run_client_get(error_rate.error_rate)

    ui.button('Execute Get', on_click=execute_get).bind_visibility_from(error_rate, 'visible')

    # Create a button to execute the Push option
    def execute_push():
        run_client_push(error_rate.error_rate)

    ui.button('Execute Push', on_click=execute_push).bind_visibility_from(error_rate, 'visible')

# Run the NiceGUI server
create_ui()
ui.run()