import pandas as pd
import matplotlib.pyplot as plt

# Use the Agg backend for matplotlib
plt.switch_backend('Agg')

# Load the CSV file
df = pd.read_csv('performance_results.csv')

# Plot Completion Time
plt.figure(figsize=(10, 6))
for error_type in df['Error Type'].unique():
    subset = df[df['Error Type'] == error_type]
    plt.plot(subset['Error Rate'], subset['Completion Time (s)'], label=f'Error Type {error_type}')
plt.xlabel('Error Rate (%)')
plt.ylabel('Completion Time (s)')
plt.title('Completion Time vs Error Rate')
plt.legend()
plt.grid(True)
plt.savefig('completion_time_vs_error_rate.png')  # Save the plot as an image

# Plot Throughput
plt.figure(figsize=(10, 6))
for error_type in df['Error Type'].unique():
    subset = df[df['Error Type'] == error_type]
    plt.plot(subset['Error Rate'], subset['Throughput (bytes/s)'], label=f'Error Type {error_type}')
plt.xlabel('Error Rate (%)')
plt.ylabel('Throughput (bytes/s)')
plt.title('Throughput vs Error Rate')
plt.legend()
plt.grid(True)
plt.savefig('comparison_vs_error_rate.png')  # Save the plot as an image