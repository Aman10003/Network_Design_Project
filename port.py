# This code was mostly created by chat-gpt 4o model
import psutil


def get_open_ports():
    """Returns a set of open ports."""
    open_ports = set()
    for conn in psutil.net_connections(kind='inet'):
        open_ports.add(conn.laddr.port)
    return open_ports


def find_unused_port(start_port=8000, end_port=9000):
    """Finds and returns an unused port within the specified range."""
    open_ports = get_open_ports()

    for port in range(start_port, end_port + 1):
        if port not in open_ports:
            return port  # Return the first unused port
    return None  # No available ports


# Example usage
if __name__ == "__main__":
    # Lists all open ports
    open_ports = get_open_ports()
    print("Open ports:", open_ports)

    # Returns the first single port
    unused_port = find_unused_port()
    if unused_port:
        print("Found unused port:", unused_port)
    else:
        print("No unused ports available.")
