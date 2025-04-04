import pandas as pd
import matplotlib.pyplot as plt

def plot_csv(filename, x_col, y_col, title, xlabel, ylabel, output=None):
    df = pd.read_csv(filename)
    plt.figure(figsize=(8, 5))
    plt.plot(df[x_col], df[y_col], marker='o')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    if output:
        plt.savefig(output)
    plt.show()

# Chart 1: Completion Time vs Error Rate
plot_csv(
    'chart1_error_rate.csv',
    'Error Rate',
    'Completion Time (s)',
    'Chart 1: Completion Time vs Error Rate',
    'Error Rate',
    'Time (s)',
    output='chart1.png'
)

# Chart 2: Completion Time vs Timeout
plot_csv(
    'chart2_timeout.csv',
    'Timeout (s)',
    'Completion Time (s)',
    'Chart 2: Completion Time vs Timeout',
    'Timeout (s)',
    'Time (s)',
    output='chart2.png'
)

# Chart 3: Completion Time vs Window Size
plot_csv(
    'chart3_window_size.csv',
    'Window Size',
    'Completion Time (s)',
    'Chart 3: Completion Time vs Window Size',
    'Window Size',
    'Time (s)',
    output='chart3.png'
)

# Chart 4: Throughput vs Error Rate
plot_csv(
    'chart4_throughput_error_rate.csv',
    'Error Rate',
    'Throughput (bytes/s)',
    'Chart 4: Throughput vs Error Rate',
    'Error Rate',
    'Throughput (Bps)',
    output='chart4.png'
)
