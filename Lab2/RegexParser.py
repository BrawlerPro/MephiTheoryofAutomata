from typing import Iterator
from RegexNode import RegexNode, RegexOp
from RegexToken import Token, TokenType


class RegexParser:
    def __init__(self, tokens: Iterator[Token]):
        self.tokens = tokens
        self.current_token: Token = next(self.tokens)  # получаем первый токен заранее

    def current(self) -> Token:
        return self.current_token

    def advance(self):
        self.current_token = next(self.tokens)  # просто берём следующий токен из генератора

    def expect(self, type_: TokenType):
        if self.current().type != type_:
            raise SyntaxError(f"Expected {type_}, got {self.current()}")
        self.advance()

    def parse(self) -> RegexNode:
        node = self.parse_expression()
        if self.current().type != TokenType.EOF:
            raise SyntaxError("Unexpected token after expression")
        return node

    def match(self, token_type: TokenType) -> bool:
        if self.current().type == token_type:
            self.advance()
            return True
        return False

    def parse_suffix(self, node: RegexNode) -> RegexNode:
        while True:
            tok = self.current()
            if tok.type == TokenType.OPTIONAL:
                self.advance()
                node = RegexNode(RegexOp.OPTIONAL, children=[node])
            elif tok.type == TokenType.REPEAT:
                self.advance()
                node = RegexNode(RegexOp.REPEAT, value=tok.value, children=[node])
            elif tok.type == TokenType.KLEENE:
                self.advance()
                node = RegexNode(RegexOp.KLEENE, children=[node])
            else:
                break
        return node

    def parse_expression(self) -> RegexNode:
        terms = [self.parse_concat()]
        while self.match(TokenType.OR):
            terms.append(self.parse_concat())
        if len(terms) == 1:
            return terms[0]
        return RegexNode(RegexOp.ALT, children=terms)

    def parse_concat(self) -> RegexNode:
        nodes = []

        while True:
            if self.current().type in (
                TokenType.CHAR, TokenType.LPAREN,
                TokenType.NAMED_GROUP_START, TokenType.NAMED_REF
            ):
                atom = self.parse_atom()
                suffix = self.parse_suffix(atom)
                nodes.append(suffix)
            else:
                break
        if not nodes:
            raise SyntaxError("Expected expression")
        elif len(nodes) == 1:
            return nodes[0]
        return RegexNode(RegexOp.CONCAT, children=nodes)

    def parse_atom(self) -> RegexNode:
        tok = self.current()

        if tok.type == TokenType.CHAR:
            self.advance()
            return RegexNode(RegexOp.CHAR, value=tok.value)

        elif tok.type == TokenType.LPAREN:
            self.advance()
            node = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return node

        elif tok.type == TokenType.NAMED_GROUP_START:
            name = tok.value
            self.advance()
            inner = self.parse_expression()
            self.expect(TokenType.RPAREN)
            group_node = RegexNode(RegexOp.NAMED_GROUP, name=name, children=[inner])
            return self.parse_suffix(group_node)

        elif tok.type == TokenType.NAMED_REF:
            self.advance()
            return RegexNode(RegexOp.NAMED_REF, name=tok.value)

        raise SyntaxError(f"Unexpected token: {tok}")
