import matplotlib.pyplot as plt
import numpy as np


def plot_tcp_metrics(sender):
    """
    Generate plots for TCP metrics from a simulation run

    Args:
        sender: TCPSender instance with collected metrics
    """
    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))

    # Check if we have any data points
    if not hasattr(sender, 'time_points') or len(sender.time_points) == 0:
        print("Warning: No time points available for plotting")
        # Create empty plots with appropriate labels
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Congestion Window Size (MSS)')
        ax1.set_title('Congestion Window Size vs Time (No Data Available)')
        ax1.grid(True)

        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Sample RTT (s)')
        ax2.set_title('Sample RTT vs Time (No Data Available)')
        ax2.grid(True)

        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('RTO (s)')
        ax3.set_title('Retransmission Timeout (RTO) vs Time (No Data Available)')
        ax3.grid(True)
    else:
        # Plot 1: Congestion Window Size vs Time
        if hasattr(sender, 'cwnd_values') and len(sender.cwnd_values) > 0:
            # Make sure we have matching lengths
            plot_length = min(len(sender.time_points), len(sender.cwnd_values))
            ax1.plot(sender.time_points[:plot_length], sender.cwnd_values[:plot_length], 'b-')
            ax1.set_title('Congestion Window Size vs Time')
        else:
            ax1.set_title('Congestion Window Size vs Time (No Data Available)')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Congestion Window Size (MSS)')
        ax1.grid(True)

        # Plot 2: Sample RTT vs Time
        if hasattr(sender, 'rtt_samples') and len(sender.rtt_samples) > 0:
            # Make sure we have matching lengths
            plot_length = min(len(sender.time_points), len(sender.rtt_samples))
            ax2.plot(sender.time_points[:plot_length], sender.rtt_samples[:plot_length], 'r-')
            ax2.set_title('Sample RTT vs Time')
        else:
            ax2.set_title('Sample RTT vs Time (No Data Available)')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Sample RTT (s)')
        ax2.grid(True)

        # Plot 3: RTO vs Time
        if hasattr(sender, 'rto_values') and len(sender.rto_values) > 0:
            # Make sure we have matching lengths
            plot_length = min(len(sender.time_points), len(sender.rto_values))
            ax3.plot(sender.time_points[:plot_length], sender.rto_values[:plot_length], 'g-')
            ax3.set_title('Retransmission Timeout (RTO) vs Time')
        else:
            ax3.set_title('Retransmission Timeout (RTO) vs Time (No Data Available)')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('RTO (s)')
        ax3.grid(True)

    plt.tight_layout()
    plt.savefig('tcp_metrics.png')
    plt.show()
