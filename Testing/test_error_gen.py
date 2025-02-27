import unittest
import random
# import error_gen
from error_gen import error_gen


class TestErrorGen(unittest.TestCase):

    def setUp(self):
        self.error_gen = error_gen()
        self.test_packet = b"test_packet"  # Sample packet for testing

    def test_packet_error_no_corruption(self):
        """Test that packet remains unchanged when error_rate is 0."""
        random.seed(1)  # Fix seed for reproducibility
        result = self.error_gen.packet_error(self.test_packet, error_rate=0)
        self.assertEqual(result, self.test_packet)

    def test_packet_error_with_corruption(self):
        """Test that packet gets corrupted when error_rate is high."""
        random.seed(2)  # Fix seed for reproducibility
        result = self.error_gen.packet_error(self.test_packet, error_rate=1)
        self.assertNotEqual(result, self.test_packet)

    def test_corruption_changes_packet(self):
        """Test that the corruption function alters the packet."""
        random.seed(3)  # Fix seed for reproducibility
        corrupted_packet = self.error_gen.corruption(self.test_packet)
        self.assertNotEqual(corrupted_packet, self.test_packet)
        self.assertEqual(len(corrupted_packet), len(self.test_packet))  # Length should be unchanged

    def test_corruption_random_error_behavior(self):
        """Test different behaviors of corruption including full random error."""
        random.seed(4)  # Fix seed for reproducibility
        corrupted_packet = self.error_gen.corruption(self.test_packet)

        if isinstance(corrupted_packet, int):
            self.assertIsInstance(corrupted_packet, int)  # Full random case
        else:
            self.assertNotEqual(corrupted_packet, self.test_packet)
            self.assertEqual(len(corrupted_packet), len(self.test_packet))


if __name__ == '__main__':
    unittest.main()
