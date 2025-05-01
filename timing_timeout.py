import matplotlib.pyplot as plt
import numpy as np
import time
from Client import Client


def measure_completion_time(timeout_ms, error_rate=0.1):
    """Measure file transfer completion time with given timeout value"""
    client = Client()
    start_time = time.time()
    try:
        client.get_file_with_tcp('random', error_rate, timeout_ms / 1000.0)
    except Exception as e:
        print(f"Error during transfer with timeout={timeout_ms}ms: {e}")
        # If an error occurs, we'll still measure the time but note the failure
    end_time = time.time()
    return end_time - start_time


def plot_timeout_performance():
    timeout_values = np.linspace(10, 100, 10)  # 10ms to 100ms
    completion_times = []

    for timeout in timeout_values:
        time = measure_completion_time(timeout)
        completion_times.append(time)
        print(f"Timeout: {timeout:.1f}ms, Completion time: {time:.2f}s")

    plt.figure(figsize=(10, 6))
    plt.plot(timeout_values, completion_times, 'o-')
    plt.xlabel('Timeout Value (ms)')
    plt.ylabel('Completion Time (s)')
    plt.title('Completion Time vs Timeout Value')
    plt.grid(True)
    plt.savefig('completion_vs_timeout.png')
    plt.show()


if __name__ == "__main__":
    plot_timeout_performance()
