class Transaction:
    def __init__(self, from_acc, to_acc, amount):
        self.from_acc = from_acc
        self.to_acc = to_acc
        self.amount = amount
        self.status = "PENDING"

class TransactionManager:
    @staticmethod
    def process_transfer(transaction):
        if transaction.from_acc.balance >= transaction.amount:
            transaction.from_acc.withdraw(transaction.amount)
            transaction.to_acc.deposit(transaction.amount)
            transaction.status = "SUCCESS"
            return True
        else:
            transaction.status = "FAILED"
            return False
