import random

class error_gen:

    def packet_error(self, packet, error_rate: float = 0):
        state = random.random()
        if state < error_rate:
            return self.corruption(packet)
        else:
            return packet

    def corruption(self, packet):
        error = random.randint(0, 3)
        length = packet.bit_length()
        # Will follow error by single bit, double bit, triple bit, or full corruption if 0
        if error == 0:
            return random.getrandbits(length)
        else:
            for i in error:





