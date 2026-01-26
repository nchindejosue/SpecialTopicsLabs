from .tokens import TokenType

class CeilParser:
    def __init__(self):
        self.tokens = []
        self.pos = 0

    def set_tokens(self, tokens):
        self.tokens = tokens
        self.pos = 0
        return self

    def consume(self, expected_type=None):
        if self.pos >= len(self.tokens):
            raise Exception("Unexpected EOF")
        token = self.tokens[self.pos]
        if expected_type and token.type != expected_type:
            raise Exception(f"Expected {expected_type}, got {token.type}")
        self.pos += 1
        return token

    def consume_string_or_word(self):
        token = self.tokens[self.pos]
        if token.type not in [TokenType.STRING, TokenType.WORD]:
            raise Exception(f"Expected STRING or WORD, got {token.type}")
        self.pos += 1
        return token

    def parse(self):
        ast = []
        while self.pos < len(self.tokens) and self.tokens[self.pos].type != TokenType.EOF:
            t = self.tokens[self.pos].type
            if t == TokenType.CREATE:
                self.consume()
                ast.append({'type': 'CREATE', 'file': self.consume_string_or_word().value, 'content': self.consume(TokenType.BLOCK).value})
            elif t == TokenType.PATCH:
                self.consume()
                ast.append({
                    'type': 'PATCH', 
                    'file': self.consume_string_or_word().value,
                    'search': (self.consume(TokenType.SEARCH), self.consume(TokenType.BLOCK))[1].value,
                    'replace': (self.consume(TokenType.REPLACE), self.consume(TokenType.BLOCK))[1].value
                })
            elif t == TokenType.DELETE:
                self.consume()
                ast.append({'type': 'DELETE', 'file': self.consume_string_or_word().value})
            elif t == TokenType.RUN:
                self.consume()
                ast.append({'type': 'RUN', 'file': self.consume_string_or_word().value})
            elif t == TokenType.FETCH_FIGMA:
                self.consume()
                ast.append({'type': 'FETCH_FIGMA', 'url': self.consume_string_or_word().value})
            else:
                self.pos += 1
        return ast
