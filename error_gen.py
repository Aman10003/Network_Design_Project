import random


class error_gen:

    def packet_error(self, packet, error_rate: float = 0):
        state = random.random()
        if state < error_rate:
            print(f">>> Corrupting packet (Triggered at error_rate={error_rate})")  # Debug
            return self.corruption(packet)
        else:
            print(">>> Sending packet without errors.")  # Debug
            return packet

    def corruption(self, packet: bytes):
        """Simulate corruption on a packet's byte."""
        # Convert bytes to a mutable bytearray
        packet = bytearray(packet)
        length = len(packet)

        # Determine how many bits to flip (1-3 random bits) if zero, then all bits are randomized
        error_count = random.randint(0, 3)
        if error_count == 0:
            print("Full Random Error")  # Debug
            return random.getrandbits(length)
        else:
            print(str(error_count) + " bit errors")  # Debug
            for _ in range(error_count):
                # Choose a random byte and bit to flip
                byte_index = random.randint(0, length - 1)  # Random byte
                bit_index = random.randint(0, 7)  # Random bit within the byte

                # Flip the chosen bit in the chosen byte
                packet[byte_index] ^= (1 << bit_index)  # XOR with bit mask

        # Return the corrupted bytes
        return bytes(packet)
