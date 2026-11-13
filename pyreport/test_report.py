import unittest

from report import mean


class MeanTest(unittest.TestCase):
    def test_mean_of_two(self):
        self.assertEqual(mean([2.0, 4.0]), 3.0)

    def test_mean_of_one(self):
        self.assertEqual(mean([5.0]), 5.0)


if __name__ == "__main__":
    unittest.main()
