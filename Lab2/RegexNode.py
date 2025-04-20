from enum import Enum
from typing import Optional, List, Union


class RegexOp(Enum):
    CHAR = 'char'                 # один символ
    CONCAT = 'concat'             # конкатенация
    ALT = 'alt'                   # альтернатива |
    KLEENE = 'kleene'             # замыкание …
    OPTIONAL = 'optional'         # ?
    REPEAT = 'repeat'             # {x}
    GROUP = 'group'               # (r)
    NAMED_GROUP = 'named_group'   # (<name>r)
    NAMED_REF = 'named_ref'       # <name>


class RegexNode:
    def __init__(
        self,
        op: RegexOp,
        value: Optional[Union[str, int]] = None,
        children: Optional[List['RegexNode']] = None,
        name: Optional[str] = None
    ):
        self.op = op
        self.value = value
        self.children = children or []
        self.name = name

    def __repr__(self, level=0):
        indent = '  ' * level
        base = f"{self.op.name}"
        if self.value is not None:
            base += f"({self.value})"
        if self.name is not None:
            base += f"<{self.name}>"
        if not self.children:
            return indent + base
        return indent + base + "(\n" + ",\n".join(
            child.__repr__(level + 1) for child in self.children
        ) + "\n" + indent + ")"
