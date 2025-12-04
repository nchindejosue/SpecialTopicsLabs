import unittest
from banking_system.account import Account
from banking_system.transaction import Transaction, TransactionManager

class TestBanking(unittest.TestCase):
    def setUp(self):
        self.acc1 = Account("A", 1000)
        self.acc2 = Account("B", 500)

    def test_successful_transfer(self):
        t = Transaction(self.acc1, self.acc2, 200)
        # Using the TransactionManager explicitly
        result = TransactionManager.process_transfer(t)
        self.assertTrue(result)
        self.assertEqual(self.acc1.balance, 800)
        self.assertEqual(self.acc2.balance, 700)
        self.assertEqual(t.status, "SUCCESS")

    def test_failed_transfer(self):
        t = Transaction(self.acc1, self.acc2, 2000)
        result = TransactionManager.process_transfer(t)
        self.assertFalse(result)
        self.assertEqual(self.acc1.balance, 1000)
        self.assertEqual(t.status, "FAILED")
