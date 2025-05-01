import time
from Client import Client
from plot_tcp_metrics import plot_tcp_metrics
import subprocess
import os

def generate_single_run_graphs():
    """Generate graphs from a single TCP simulation run"""
    print("Running a single TCP file transfer to collect metrics...")
    client = Client()

    # Use moderate error rate for interesting graphs
    sender = client.get_file_with_tcp(error_type='random', error_rate=0.1)

    # Generate the three required graphs
    plot_tcp_metrics(sender)
    print("Single run graphs generated and saved as 'tcp_metrics.png'")

def generate_performance_plots():
    """Generate Phase 5 performance plots"""
    print("\nGenerating performance plots...")

    # Run timing_error_rate.py
    print("\nRunning timing_error_rate.py...")
    subprocess.run(["python", "timing_error_rate.py"])
    print("Completion Time vs Error Rate plot generated and saved as 'completion_vs_error_rate.png'")

    # Run timing_timeout.py
    print("\nRunning timing_timeout.py...")
    subprocess.run(["python", "timing_timeout.py"])
    print("Completion Time vs Timeout Value plot generated and saved as 'completion_vs_timeout.png'")

    # Run timing_window_size.py
    print("\nRunning timing_window_size.py...")
    subprocess.run(["python", "timing_window_size.py"])
    print("Completion Time vs Window Size plot generated and saved as 'completion_vs_window_size.png'")

if __name__ == "__main__":
    print("TCP Implementation Evaluation Graphs Generator")
    print("=============================================")

    # Check if server is running
    print("Note: Make sure the server is running before proceeding.")
    input("Press Enter to continue...")

    # Generate single run graphs
    generate_single_run_graphs()

    # Generate performance plots
    generate_performance_plots()

    print("\nAll graphs have been generated successfully!")
    print("\nGenerated files:")
