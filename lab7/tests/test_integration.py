import unittest
from banking_system.account import Account
from banking_system.transaction import Transaction, TransactionManager

class TestIntegration(unittest.TestCase):
    def test_money_transfer(self):
        acc1 = Account("A", 500)
        acc2 = Account("B", 100)
        t = Transaction(acc1, acc2, 200)
        success = TransactionManager.process_transfer(t)
        self.assertTrue(success)
        self.assertEqual(acc1.balance, 300)

    def test_transfer_fail(self):
        acc1 = Account("A", 50)
        acc2 = Account("B", 100)
        t = Transaction(acc1, acc2, 200)
        success = TransactionManager.process_transfer(t)
        self.assertFalse(success)
