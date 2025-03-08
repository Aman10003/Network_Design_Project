# Python packages
from nicegui import ui
import subprocess
from socket import *
import sys
import port as p
import threading  # Use threading instead of multiprocessing
import time
# Files in the project
import send
import receive


class gui:

    def __init__(self):
        self.server_name = 'localhost'
        self.server_port = 12000
        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        self.error_type = None
        self.error_rate = None
        self.state = None
        self.error_rate_value = None
        self.error_rate_label = None
        self.error_type_name = None

    def run_server(self):
        # Creating a separate thread for running the server
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()  # Start the server in a new thread

    def start_server(self):
        # This function will be run in a separate thread
        python_executable = sys.executable  # Get the path to the current Python interpreter
        subprocess.Popen([python_executable, 'Server.py'])

    def run_client_hello(self):
        message = 'HELLO'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        try:
            server_message, _ = self.client_socket.recvfrom(2048)
            self.response_textbox.value += f'HELLO Response: {server_message.decode()}\n'  # Append server response to text box
            print(server_message.decode())
        except ConnectionResetError:
            self.response_textbox.value += 'Connection was forcibly closed by the server.\n'

    def run_client_get(self):
        message = 'GET'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))

        message = str([self.error_type.value, self.error_rate.value])
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))

        r = receive.receive()
        r.udp_receive(self.client_socket, False, self.error_type.value, self.error_rate.value)
        self.response_textbox.value += f'GET Response: Test\n'  # Append server response to text box

    def run_client_push(self):
        message = 'PUSH'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        s = send.send()



        def send_with_progress():
            total_packets, retransmissions, duplicate_acks = s.udp_send_with_progress(
                self.client_socket,
                (self.server_name, self.server_port),
                self.error_type.value,
                self.error_rate.value,
                self.update_progress
            )

            ui.notify(f"Transfer Completed: {total_packets} packets sent!")
            self.progress_bar.set_value(1.0)  # Set progress to 100%

        threading.Thread(target=send_with_progress, daemon=True).start()

    def update_progress(self, progress, retransmissions, duplicate_acks):
        """Update UI dynamically."""
        self.progress_bar.set_value(progress)
        self.retrans_label.set_text(f"Retransmissions: {retransmissions}")
        self.dup_ack_label.set_text(f"Duplicate ACKs: {duplicate_acks}")

    def stop_server(self):
        message = 'END'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.client_socket.close()
        self.response_textbox.value += 'Server stopped.\n'  # Append server stop message to text box

    def get_control(self):
        self.error_control(True)
        self.state = 'get'

    def push_control(self):
        self.error_control(True)
        self.state = 'push'

    def execute(self):
        if self.state == 'get':
            self.run_client_get()
        elif self.state == 'push':
            self.run_client_push()

    def error_control(self, value):
        self.error_rate_label.visible = value
        self.error_rate.visible = value
        self.error_rate_value.visible = value
        self.error_type_name = value

    def create_ui(self):
        self.response_textbox = ui.textarea(label='Server Responses')

        with ui.row():
            ui.button('Start Server', on_click=self.run_server)  # Start server now runs in a separate thread
            ui.button('Send HELLO from Client', on_click=self.run_client_hello)
            ui.button('Stop Server', on_click=self.stop_server)

        with ui.row():
            get_button = ui.button('Get', on_click=self.get_control)
            push_button = ui.button('Push', on_click=self.push_control)

        # Create a label and slider for selecting error rate (only visible when Get or Push)
        with ui.column():
            with ui.row():
                self.error_type = ui.select([1, 2, 3], value=1)
                self.error_type.visible = False
                self.error_type_name = ui.select({1: 'No Error', 2: 'Ack Error', 3: 'Data Error'}).bind_value(self.error_type, 'value')
            self.error_rate_label = ui.label('Select Error Rate')
            self.error_rate = ui.slider(min=0, max=1, step=0.01, value=0)
            self.error_rate_value = ui.label().bind_text_from(self.error_rate, 'value')

        self.execute = ui.button("Execute", on_click=self.execute)

        # Create UI elements for progress tracking
        self.progress_bar = ui.linear_progress(value=0)
        with ui.row():
            self.retrans_label = ui.label("Retransmissions: 0")
            self.dup_ack_label = ui.label("Duplicate ACKs: 0")

    def main(self):
        self.create_ui()
        port_assignment = p.find_unused_port()
        ui.run(port=port_assignment)


# Needs __mp_main__ for ui.run (must be run in multiprocessor)
if __name__ in {"__main__", "__mp_main__"}:
    # functions.main()
    # units_def.units
    g = gui()
    g.main()
