import matplotlib.pyplot as plt
import numpy as np
import time
from Client import Client


def measure_completion_time(error_rate, error_type='random'):
    """Measure file transfer completion time with given error rate"""
    client = Client()
    start_time = time.time()
    try:
        client.get_file_with_tcp(error_type, error_rate)
    except Exception as e:
        print(f"Error during transfer with error_rate={error_rate}: {e}")
        # If an error occurs, we'll still measure the time but note the failure
    end_time = time.time()
    return end_time - start_time


def plot_error_rate_performance():
    error_rates = np.linspace(0, 0.7, 15)  # 0% to 70%
    completion_times = []

    for rate in error_rates:
        time = measure_completion_time(rate)
        completion_times.append(time)
        print(f"Error rate: {rate:.2f}, Completion time: {time:.2f}s")

    plt.figure(figsize=(10, 6))
    plt.plot(error_rates * 100, completion_times, 'o-')
    plt.xlabel('Error Rate (%)')
    plt.ylabel('Completion Time (s)')
    plt.title('Completion Time vs Error Rate')
    plt.grid(True)
    plt.savefig('completion_vs_error_rate.png')
    plt.show()


if __name__ == "__main__":
    plot_error_rate_performance()
