# Configuration value to select checksum method
# 0 for XOR checksum, 1 for CRC-16
CHECKSUM_METHOD = 0

def compute_xor_checksum(data):
    """Calculate a 16-bit XOR checksum."""
    checksum = 0
    for byte in data:
        checksum ^= byte
        checksum &= 0xFFFF  # Ensure that the checksum stays within 16 bits
    return checksum

def compute_crc16(data):
    """Calculate a 16-bit CRC using the polynomial 0x8005."""
    crc = 0xFFFF
    polynomial = 0x8005
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFFFF  # Ensure that the CRC stays within 16 bits
    return crc

def compute_checksum(data):
    if CHECKSUM_METHOD == 0:
        return compute_xor_checksum(data)
    elif CHECKSUM_METHOD == 1:
        return compute_crc16(data)
    else:
        raise ValueError("Invalid checksum method selected.")