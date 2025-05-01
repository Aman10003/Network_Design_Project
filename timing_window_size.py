import matplotlib.pyplot as plt
import numpy as np
import time
from Client import Client


def measure_completion_time(window_size, error_rate=0.1):
    """Measure file transfer completion time with given window size"""
    client = Client()
    start_time = time.time()
    try:
        client.get_file_with_tcp('random', error_rate, window_size=window_size)
    except Exception as e:
        print(f"Error during transfer with window_size={window_size}: {e}")
        # If an error occurs, we'll still measure the time but note the failure
    end_time = time.time()
    return end_time - start_time


def plot_window_size_performance():
    window_sizes = np.arange(1, 51)  # 1 to 50
    completion_times = []

    for size in window_sizes:
        time = measure_completion_time(size)
        completion_times.append(time)
        print(f"Window size: {size}, Completion time: {time:.2f}s")

    plt.figure(figsize=(10, 6))
    plt.plot(window_sizes, completion_times, 'o-')
    plt.xlabel('Window Size')
    plt.ylabel('Completion Time (s)')
    plt.title('Completion Time vs Window Size')
    plt.grid(True)
    plt.savefig('completion_vs_window_size.png')
    plt.show()


if __name__ == "__main__":
    plot_window_size_performance()
