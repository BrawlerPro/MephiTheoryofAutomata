import re
from typing import List
from RegexToken import *


class RegexLexer:
    def __init__(self, input_string: str):
        self.input = input_string
        self.pos = 0
        self.length = len(input_string)

    def next_char(self):
        if self.pos >= self.length:
            return ''
        return self.input[self.pos]

    def advance(self):
        self.pos += 1

    def match(self, s: str) -> bool:
        return self.input.startswith(s, self.pos)

    def lex(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            c = self.next_char()

            # Экранированные метасимволы: %s%
            if c == '%' and self.pos + 2 < self.length and self.input[self.pos + 2] == '%':
                esc_char = self.input[self.pos + 1]
                tokens.append(Token(TokenType.CHAR, esc_char))
                self.pos += 3
                continue

            # Альтернатива
            if c == '|':
                tokens.append(Token(TokenType.OR))
                self.advance()
                continue

            # Клини (…)
            if self.match('…'):
                tokens.append(Token(TokenType.KLEENE))
                self.pos += 1  # только один символ
                continue

            # Опциональная часть
            if c == '?':
                tokens.append(Token(TokenType.OPTIONAL))
                self.advance()
                continue

            # Повтор {x}
            if c == '{':
                end = self.input.find('}', self.pos)
                if end == -1:
                    raise ValueError("Unclosed repeat {x}")
                repeat_count = self.input[self.pos + 1:end]
                if not repeat_count.isdigit():
                    raise ValueError(f"Invalid repeat count: {repeat_count}")
                tokens.append(Token(TokenType.REPEAT, int(repeat_count)))
                self.pos = end + 1
                continue

            # Группа с именем (<name>
            if self.match('(<'):
                name_end = self.input.find('>', self.pos + 2)
                if name_end == -1:
                    raise ValueError("Unclosed named group (<name>")
                group_name = self.input[self.pos + 2:name_end]
                if not re.fullmatch(r'\w+', group_name):
                    raise ValueError(f"Invalid group name: {group_name}")
                tokens.append(Token(TokenType.NAMED_GROUP_START, group_name))
                self.pos = name_end + 1
                continue

            # Использование именованной группы <name>
            if c == '<':
                name_end = self.input.find('>', self.pos)
                if name_end == -1:
                    raise ValueError("Unclosed named reference <name>")
                group_name = self.input[self.pos + 1:name_end]
                tokens.append(Token(TokenType.NAMED_REF, group_name))
                self.pos = name_end + 1
                continue

            # Обычные скобки
            if c == '(':
                tokens.append(Token(TokenType.LPAREN))
                self.advance()
                continue

            if c == ')':
                tokens.append(Token(TokenType.RPAREN))
                self.advance()
                continue

            # Все остальное — обычный символ
            tokens.append(Token(TokenType.CHAR, c))
            self.advance()

        tokens.append(Token(TokenType.EOF))
        return tokens
