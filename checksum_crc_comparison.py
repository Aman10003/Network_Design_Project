import time
import pandas as pd
from checksums import compute_xor_checksum, compute_crc16

class ChecksumCRCComparison:
    def __init__(self):
        self.results = []  # Store results for comparison
        self.retransmissions_xor = 0
        self.retransmissions_crc = 0

    def test_error_detection(self, data, injected_error=False):
        # Compute correct checksums BEFORE corruption
        correct_xor = compute_xor_checksum(data)
        correct_crc = compute_crc16(data)

        # Inject error if required
        if injected_error:
            data = bytearray(data)
            data[0] ^= 0xFF  # Flip bits in the first byte
            print(f"Injected Error in Data: {data}")  # Debugging Line
            data = bytes(data)

        start_time = time.time()
        xor_checksum = compute_xor_checksum(data)
        xor_time = time.time() - start_time

        start_time = time.time()
        crc_checksum = compute_crc16(data)
        crc_time = time.time() - start_time

        xor_detected = xor_checksum == correct_xor
        crc_detected = crc_checksum == correct_crc

        print(f"Original XOR: {correct_xor}, Computed XOR: {xor_checksum}")
        print(f"Original CRC: {correct_crc}, Computed CRC: {crc_checksum}")

        if xor_checksum != correct_xor:
            self.retransmissions_xor += 1
            print("XOR Checksum mismatch! Retransmission triggered.")
        if crc_checksum != correct_crc:
            self.retransmissions_crc += 1
            print("CRC-16 Checksum mismatch! Retransmission triggered.")

        self.results.append({
            "Injected Error": injected_error,
            "XOR Checksum Detected": xor_detected,
            "CRC-16 Detected": crc_detected,
            "XOR Time (ms)": xor_time * 1000,
            "CRC Time (ms)": crc_time * 1000,
            "XOR Retransmissions": self.retransmissions_xor,
            "CRC Retransmissions": self.retransmissions_crc
        })

    def run_tests(self, num_tests=100):
        sample_data = b"Hello World! This is a test data for checksum validation."
        for _ in range(num_tests // 2):
            self.test_error_detection(sample_data, injected_error=False)
            self.test_error_detection(sample_data, injected_error=True)
        self.generate_report()

    def generate_report(self):
        df = pd.DataFrame(self.results)
        file_path = "checksum_crc_comparison.csv"
        df.to_csv(file_path, index=False)
        print(f"Report saved at: {file_path} with retransmission data included.")

if __name__ == "__main__":
    comparison = ChecksumCRCComparison()
    comparison.run_tests()
