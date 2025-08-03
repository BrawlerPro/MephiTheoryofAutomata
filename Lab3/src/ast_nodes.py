# src/ast.py

class ASTNode:
    """Базовый класс всех узлов AST."""
    pass


class Program(ASTNode):
    def __init__(self, directives):
        # directives: list of VarDecl, ConstDecl, MapDecl, ProcDecl or statements
        self.directives = directives

    def __repr__(self):
        return f"Program({self.directives!r})"


class VarDecl(ASTNode):
    def __init__(self, typ, name, expr):
        # typ: 'INT' or 'BOOLEAN'
        self.typ = typ
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f"VarDecl({self.typ}, {self.name!r}, {self.expr!r})"


class ConstDecl(ASTNode):
    def __init__(self, typ, name, expr):
        # typ: 'CINT' or 'CBOOLEAN'
        self.typ = typ
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f"ConstDecl({self.typ}, {self.name!r}, {self.expr!r})"


class MapDecl(ASTNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"MapDecl({self.name!r})"


class ProcDecl(ASTNode):
    def __init__(self, name, params, body):
        # params: list of identifier strings
        # body: Block
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        return f"ProcDecl({self.name!r}, params={self.params!r}, body={self.body!r})"


class Block(ASTNode):
    def __init__(self, statements):
        # statements: list of statement-nodes
        self.statements = statements

    def __repr__(self):
        return f"Block({self.statements!r})"


class Assign(ASTNode):
    def __init__(self, name, expr):
        # name: identifier string
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f"Assign({self.name!r}, {self.expr!r})"


class IncDec(ASTNode):
    def __init__(self, op, target, value):
        # op: 'INC' or 'DEC'
        # target: ASTNode (VarRef, ProcCall or expression)
        # value: ASTNode (literal, VarRef, ProcCall or logic expr)
        self.op = op
        self.target = target
        self.value = value

    def __repr__(self):
        return f"IncDec({self.op}, {self.target!r}, {self.value!r})"


class IfStmt(ASTNode):
    def __init__(self, cond, then_block, else_block=None):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block

    def __repr__(self):
        return f"IfStmt(cond={self.cond!r}, then={self.then_block!r}, else={self.else_block!r})"


class WhileStmt(ASTNode):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block

    def __repr__(self):
        return f"WhileStmt(cond={self.cond!r}, block={self.block!r})"


class ProcCall(ASTNode):
    def __init__(self, name, args):
        # name: identifier string
        # args: list of ASTNode
        self.name = name
        self.args = args

    def __repr__(self):
        return f"ProcCall({self.name!r}, args={self.args!r})"


class RobotOp(ASTNode):
    def __init__(self, op, direction=None):
        # op: 'STEP','BACK','RIGHT','LEFT','LOOK'
        # direction: for STEP — one of 'NORTH','SOUTH','EAST','WEST'
        self.op = op
        self.direction = direction

    def __repr__(self):
        return f"RobotOp({self.op!r}, dir={self.direction!r})"


class MapOp(ASTNode):
    def __init__(self, op, res_var, map_name, x, y):
        self.op = op
        self.res_var = res_var
        self.map_name = map_name
        self.x = x
        self.y = y

    def __repr__(self):
        return f"MapOp({self.op!r}, {self.res_var!r}, {self.x!r}, {self.y!r})"


class BinaryOp(ASTNode):
    def __init__(self, op, left, right):
        # op: '+','-','INC','DEC','OR','GT','LT'
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.op!r}, {self.left!r}, {self.right!r})"


class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        # op: 'NOT'
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.op!r}, {self.operand!r})"


class IntLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"IntLiteral({self.value})"


class PrintStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"PrintStmt({self.expr!r})"


class BoolLiteral(ASTNode):
    def __init__(self, value: bool):
        self.value = value

    def __repr__(self):
        return f"BoolLiteral({self.value})"


class VarRef(ASTNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"VarRef({self.name!r})"
