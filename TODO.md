TODO:
- [ ] CRC checksum (library) \
• Implement CRC-16 using the standard polynomial (0x8005).
• Replace the existing checksum function with CRC-16 and re-run the program.
• Compare the performance of checksum vs. CRC-16 based on:
 Error detection capability: Measure how many errors each method fails to
detect.
 Computational overhead: Measure execution time for both checksum
methods.
 Impact on retransmissions: Count the number of retransmitted packets
under both methods.
• Generate a comparison table summarizing the findings
- [ ] Error detection
- [ ] Random packet delay (Maybe done)
- [ ] Performance Charts 
- [ ] Measure and compare the impact of various delay ranges on:
-  Total transmission time
-  Number of retransmissions
-  Number of duplicate ACKs received
- [ ] Implement an adaptive timeout mechanism that dynamically adjusts the
retransmission timer based on observed delay trends.

- [ ] GUI \
Implement an applet/GUI to show the data transfer (display of image as the transfer happens) and the (sender and
receiver) FSM. Note: If you include a simplistic GUI that does the essentials and
nothing more (e.g., looks like it would function on Windows 95), that does not qualify
as the full 25%. You need to create something that is not only functional but has features
of a high-quality GUI. If you have any doubts about what this entails or what “high
quality” means in this context, you are more than welcome to display your GUI in office
hours before the posted due date for advice
- [ ] Progress bar
- [ ] Multithreading(Maybe have sender and recieve as its own subprocess)
- • The sender should contain:
-  A sending thread that transmits data packets.
-  A listener thread that waits for and processes ACKs.
-  The receiver should contain:
-  A processing thread to handle incoming packets and verify the checksum.
-  A response thread to send ACKs back to the sender. \
Use appropriate synchronization mechanisms (e.g., locks, semaphores, or message
queues) to ensure thread safety.
Compare the completion time of single-threaded vs. multi-threaded implementations