import unittest
from banking_system.account import Account

class TestAccount(unittest.TestCase):
    def setUp(self):
        self.acc = Account("TestUser", 100)

    def test_deposit(self):
        self.acc.deposit(50)
        self.assertEqual(self.acc.balance, 150)

    def test_withdraw_success(self):
        self.acc.withdraw(40)
        self.assertEqual(self.acc.balance, 60)

    def test_withdraw_failure(self):
        with self.assertRaises(ValueError):
            self.acc.withdraw(200)
