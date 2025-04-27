# Python packages
from nicegui import ui
import subprocess
from socket import *
import sys
import asyncio
import threading  # Use threading instead of multiprocessing
import time
# Files in the project
import send
import receive
import port as p


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
        self.response_textbox = None
        self.execute_button = None
        self.transmit_type = None
        self.transmit_type_name = None
        self.progress_bar = None
        self.retrans_label = None
        self.dup_ack_label = None
        self.ack_eff_label = None
        self.retrans_overhead_label = None

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
            # Append server response to text box
            self.response_textbox.value += f'HELLO Response: {server_message.decode()}\n'
            print(server_message.decode())
        except ConnectionResetError:
            self.response_textbox.value += 'Connection was forcibly closed by the server.\n'

    def run_client_get(self):
        message = 'GET'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))

        # Map the numeric selection to protocol string
        transmit_map = {1: "sw", 2: "gbn", 3: "sr"}
        protocol = transmit_map.get(self.transmit_type.value, "sw")

        # Send error parameters along with the protocol choice
        msg = str([self.error_type.value, self.error_rate.value, protocol])
        self.client_socket.sendto(msg.encode(), (self.server_name, self.server_port))

        r = receive.receive()
        r.udp_receive_protocol(self.client_socket, False, self.error_type.value, self.error_rate.value, protocol)
        self.response_textbox.value += f'GET Response: Image received.\n' # Append server response to text box

    def run_client_push(self):
        message = 'PUSH'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))

        transmit_map = {1: "sw", 2: "gbn", 3: "sr"}
        protocol = transmit_map.get(self.transmit_type.value, "sw")

        msg = str([self.error_type.value, self.error_rate.value, protocol])
        self.client_socket.sendto(msg.encode(), (self.server_name, self.server_port))
        s = send.send()

        def send_with_progress():
            total_packets, retransmissions, duplicate_acks, ack_efficiency, retransmission_overhead = \
                s.udp_send_protocol(
                    self.client_socket,
                    (self.server_name, self.server_port),
                    self.error_type.value,
                    self.error_rate.value,
                    protocol=protocol,
                    update_ui_callback=[self.progress_bar,
                                        self.retrans_label,
                                        self.dup_ack_label,
                                        self.ack_eff_label,
                                        self.retrans_overhead_label]
                )
            # ui.run(lambda: self.update_progress(1, retransmissions, duplicate_acks, ack_efficiency,retransmission_overhead))

            self.update_progress(1, retransmissions, duplicate_acks, ack_efficiency, retransmission_overhead)
            # Schedule notify_completion in the main event loop
            # ui.run(lambda: self.notify_completion(total_packets))

        threading.Thread(target=send_with_progress, daemon=True).start()

    async def notify_completion(self, total_packets):
        """Notify UI when transfer is complete"""
        ui.notify(f"Transfer Completed: {total_packets} packets sent!")
        self.progress_bar.set_value(1.0)  # Set progress to 100%

    def update_progress(self, progress, retransmissions, duplicate_acks, ack_efficiency=0, retransmission_overhead=0):
        """Update UI dynamically."""
        self.progress_bar.set_value(progress)
        self.retrans_label.set_text(f"Retransmissions: {retransmissions}")
        self.dup_ack_label.set_text(f"Duplicate ACKs: {duplicate_acks}")
        self.ack_eff_label.set_text(f"ACK Efficiency: {ack_efficiency:.2f} %")
        self.retrans_overhead_label.set_text(f"Retransmission Overhead: {retransmission_overhead:.2f} %")

    def stop_server(self):
        message = 'END'
        self.client_socket.sendto(message.encode(), (self.server_name, self.server_port))
        self.client_socket.close()
        self.response_textbox.value += 'Server stopped.\n'  # Append server stop message to text box

    def get_control(self):
        # self.error_control(True)
        self.state = 'get'

    def push_control(self):
        # self.error_control(True)
        self.state = 'push'

    def execute(self):
        if self.state == 'get':
            self.run_client_get()
        elif self.state == 'push':
            self.run_client_push()

    def error_control(self, value):
        # Make all error and protocol controls visible when needed
        self.error_rate_label.visible = value
        self.error_rate.visible = value
        self.error_rate_value.visible = value
        self.error_type.visible = value
        self.transmit_type.visible = value
        self.error_type_name.visible = value
        self.transmit_type_name.visible = value

    def create_ui(self):
        self.response_textbox = ui.textarea(label='Server Responses')

        with ui.row():
            ui.button('Start Server', on_click=self.run_server)  # Start server now runs in a separate thread
            ui.button('Send HELLO from Client', on_click=self.run_client_hello)
            ui.button('Stop Server', on_click=self.stop_server)

        with ui.row():
            ui.button('Get', on_click=self.get_control)
            ui.button('Push', on_click=self.push_control)

        # Create a label and slider for selecting error rate (only visible when Get or Push)
        with ui.column():
            with ui.row():
                self.error_type = ui.select([1, 2, 3, 4, 5], value=1)
                self.error_type.visible = False
                self.error_type_name = ui.select(
                    {1: 'No Error', 2: 'ACK Error', 3: 'Data Error', 4: 'ACK Lost', 5: 'Data Lost'}
                ).bind_value(self.error_type, 'value')
            self.error_rate_label = ui.label('Select Error Rate')
            self.error_rate = ui.slider(min=0, max=1, step=0.01, value=0)
            self.error_rate_value = ui.label().bind_text_from(self.error_rate, 'value')

        # Protocol selection: 1 = RDT 3.0 (Stop-and-Wait), 2 = GBN, 3 = SR
        self.transmit_type = ui.select([1, 2, 3], value=1)
        self.transmit_type.visible = False
        self.transmit_type_name = ui.select(
            {1: 'RDT 3.0', 2: 'GBN', 3: 'SR'}
        ).bind_value(self.transmit_type)

        self.execute_button = ui.button("Execute", on_click=self.execute)

        # Create UI elements for progress tracking
        self.progress_bar = ui.linear_progress(value=0)
        with ui.row():
            self.retrans_label = ui.label("Retransmissions: 0")
            self.dup_ack_label = ui.label("Duplicate ACKs: 0")
            self.ack_eff_label = ui.label("ACK Efficiency: 0.00")
            self.retrans_overhead_label = ui.label("Retransmission Overhead: 0.00")

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
