from enum import Enum, auto

class TokenType(Enum):
    CREATE = auto()
    PATCH = auto()
    DELETE = auto()
    RUN = auto()
    FETCH_FIGMA = auto()
    SEARCH = auto()
    REPLACE = auto()
    STRING = auto()
    WORD = auto()
    BLOCK = auto()
    EOF = auto()

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"
