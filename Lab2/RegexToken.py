from enum import Enum
from typing import Optional


class TokenType(Enum):
    CHAR = 'CHAR'
    OR = 'OR'
    KLEENE = 'KLEENE'
    OPTIONAL = 'OPTIONAL'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    REPEAT = 'REPEAT'
    NAMED_GROUP_START = 'NAMED_GROUP_START'
    NAMED_GROUP_END = 'NAMED_GROUP_END'
    NAMED_REF = 'NAMED_REF'
    EMPTY = "EMPTY"
    EOF = 'EOF'


class Token:
    def __init__(self, type_: TokenType, value: Optional[str] = None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"{self.type.name}({self.value})" if self.value else f"{self.type.name}"
