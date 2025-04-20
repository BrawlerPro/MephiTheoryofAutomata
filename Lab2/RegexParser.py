from typing import List
from RegexNode import RegexNode, RegexOp
from RegexToken import Token, TokenType


class RegexParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1

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

    def parse_concat(self) -> RegexNode or None:
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
            return None
        elif len(nodes) == 1:
            return nodes[0]
        return RegexNode(RegexOp.CONCAT, children=nodes)

    def parse_postfix(self) -> RegexNode:
        node = self.parse_atom()
        while True:
            tok = self.current()
            if tok.type == TokenType.KLEENE:
                self.advance()
                node = RegexNode(RegexOp.KLEENE, children=[node])
            elif tok.type == TokenType.OPTIONAL:
                self.advance()
                node = RegexNode(RegexOp.OPTIONAL, children=[node])
            elif tok.type == TokenType.REPEAT:
                self.advance()
                node = RegexNode(RegexOp.REPEAT, value=tok.value, children=[node])
            else:
                break
        return node

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
            # print(f"→ Входим в NAMED_GROUP {name}")
            inner = self.parse_expression()
            self.expect(TokenType.RPAREN)
            group_node = RegexNode(RegexOp.NAMED_GROUP, name=name, children=[inner])
            group_node_with_suffix = self.parse_suffix(group_node)
            # print(f"← Вышли из NAMED_GROUP {name}: {group_node_with_suffix}")
            return group_node_with_suffix

        elif tok.type == TokenType.NAMED_REF:
            self.advance()
            return RegexNode(RegexOp.NAMED_REF, name=tok.value)

        raise SyntaxError(f"Unexpected token: {tok}")
