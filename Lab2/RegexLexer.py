import re
from RegexToken import *
from typing import Iterator


class RegexLexer:
    def __init__(self, input_string: str):
        self.input = input_string            # исходная строка
        self.pos = 0                         # текущая позиция в строке
        self.length = len(input_string)      # длина строки

    def next_char(self):
        if self.pos >= self.length:
            return ''                        # если позиция вышла за пределы — возвращаем пустую строку
        return self.input[self.pos]          # иначе возвращаем текущий символ

    def advance(self):
        self.pos += 1                        # двигаем позицию вперёд

    def match(self, s: str) -> bool:
        return self.input.startswith(s, self.pos)  # проверка, начинается ли подстрока с позиции на `s`

    def lex(self) -> Iterator[Token]:        # генератор токенов
        while self.pos < self.length:
            c = self.next_char()            # текущий символ

            # Экранированные символы вида %s%
            if c == '%' and self.pos + 2 < self.length and self.input[self.pos + 2] == '%':
                esc_char = self.input[self.pos + 1]                 # получаем экранируемый символ
                yield Token(TokenType.CHAR, esc_char)               # возвращаем как обычный символ
                self.pos += 3                                       # пропускаем %s%
                continue

            # Альтернатива: |
            if c == '|':
                yield Token(TokenType.OR)       # возвращаем токен ИЛИ
                self.advance()
                continue

            # Клини (… — многоточие в виде одного символа)
            if self.match('…'):
                yield Token(TokenType.KLEENE)   # звезда Клини
                self.pos += 1                   # здесь у тебя один символ '…', а не три точки
                continue

            # Опциональный символ: ?
            if c == '?':
                yield Token(TokenType.OPTIONAL)
                self.advance()
                continue

            # Повтор: {n}
            if c == '{':
                end = self.input.find('}', self.pos)
                if end == -1:
                    raise ValueError("Unclosed repeat {x}")
                repeat_count = self.input[self.pos + 1:end]
                if not repeat_count.isdigit():
                    raise ValueError(f"Invalid repeat count: {repeat_count}")
                yield Token(TokenType.REPEAT, int(repeat_count))  # возвращаем повтор с числом
                self.pos = end + 1
                continue

            # Начало именованной группы: (<name>
            if self.match('(<'):
                name_end = self.input.find('>', self.pos + 2)
                if name_end == -1:
                    raise ValueError("Unclosed named group (<name>")
                group_name = self.input[self.pos + 2:name_end]
                if not re.fullmatch(r'\w+', group_name):
                    raise ValueError(f"Invalid group name: {group_name}")
                yield Token(TokenType.NAMED_GROUP_START, group_name)  # старт именованной группы
                self.pos = name_end + 1
                continue

            # Ссылка на группу: <name>
            if c == '<':
                name_end = self.input.find('>', self.pos)
                if name_end == -1:
                    raise ValueError("Unclosed named reference <name>")
                group_name = self.input[self.pos + 1:name_end]
                yield Token(TokenType.NAMED_REF, group_name)          # ссылка на именованную группу
                self.pos = name_end + 1
                continue

            # Левая скобка
            if c == '(':
                yield Token(TokenType.LPAREN)
                self.advance()
                continue

            # Правая скобка
            if c == ')':
                yield Token(TokenType.RPAREN)
                self.advance()
                continue

            # Всё остальное — обычный символ
            yield Token(TokenType.CHAR, c)
            self.advance()

        # Завершающий токен
        yield Token(TokenType.EOF)
