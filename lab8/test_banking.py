
import unittest
from banking_app import BankAccount

class TestBanking(unittest.TestCase):
    def setUp(self):
        self.acc = BankAccount("TestUser", 100)

    def test_deposit(self):
        self.acc.deposit(50)
        self.assertEqual(self.acc.get_balance(), 150)

    def test_withdraw(self):
        self.acc.withdraw(30)
        self.assertEqual(self.acc.get_balance(), 70)

    def test_overdraft(self):
        result = self.acc.withdraw(200)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
