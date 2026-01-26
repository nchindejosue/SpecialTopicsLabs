import re
from .tokens import Token, TokenType

class CeilLexer:
    def __init__(self):
        self.rules = [
            (TokenType.CREATE, r'CREATE'),
            (TokenType.PATCH, r'PATCH'),
            (TokenType.DELETE, r'DELETE'),
            (TokenType.RUN, r'RUN'),
            (TokenType.FETCH_FIGMA, r'FETCH_FIGMA'),
            (TokenType.SEARCH, r'SEARCH'),
            (TokenType.REPLACE, r'REPLACE'),
            (TokenType.BLOCK, r'<<<[\s\S]*?>>>'),
            (TokenType.STRING, r'"[^"]*"'),
            (TokenType.STRING, r"'[^']*'"),
            (TokenType.WORD, r'[a-zA-Z0-9_\./\\-]+'),
        ]

    def tokenize(self, code):
        tokens = []
        pos = 0
        while pos < len(code):
            match = None
            if code[pos].isspace():
                pos += 1
                continue
            for type, pattern in self.rules:
                regex = re.compile(pattern)
                match = regex.match(code, pos)
                if match:
                    val = match.group(0)
                    if type in [TokenType.BLOCK, TokenType.STRING]:
                        # Strip quotes or <<< >>>
                        if type == TokenType.BLOCK:
                            val = val[3:-3]
                        else:
                            val = val[1:-1]
                    tokens.append(Token(type, val))
                    pos = match.end()
                    break
            if not match:
                pos += 1 # Skip unknown
        tokens.append(Token(TokenType.EOF, None))
        return tokens
