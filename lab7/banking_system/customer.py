from banking_system.account import Account

class Customer:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.account = Account(name)
        self._is_authenticated = False

    def authenticate(self, password):
        if password == self.password:
            self._is_authenticated = True
            return True
        return False

    def is_authenticated(self):
        return self._is_authenticated
