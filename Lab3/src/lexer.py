import ply.lex as lex

# 1) Одинарные литералы
literals = ['+', '-']

# 2) Ключевые слова
reserved = {
    'int': 'KW_INT',
    'boolean': 'KW_BOOLEAN',
    'cint': 'KW_CINT',
    'cboolean': 'KW_CBOOLEAN',
    'map': 'KW_MAP',
    'proc': 'KW_PROC',
    'while': 'KW_WHILE',
    'do': 'KW_DO',
    'if': 'KW_IF',
    'else': 'KW_ELSE',
    'true': 'TRUE',
    'false': 'FALSE',
    'inc': 'OP_INC',
    'dec': 'OP_DEC',
    'not': 'OP_NOT',
    'or': 'OP_OR',
    'gt': 'OP_GT',
    'lt': 'OP_LT',
    'eq': 'OP_EQ',
    'step': 'OP_STEP',
    'back': 'OP_BACK',
    'right': 'OP_RIGHT',
    'left': 'OP_LEFT',
    'look': 'OP_LOOK',
    'bar': 'MAP_BAR',
    'emp': 'MAP_EMP',
    'set': 'MAP_SET',
    'clr': 'MAP_CLR',
    'print': 'KW_PRINT',
}

# 3) Все токены
tokens = [
             'INT_LITERAL',
             'IDENTIFIER',
             'OP_ASSIGN',
             'LPAREN',
             'RPAREN',
             'COMMA',
             'NEWLINE',
         ] + list(reserved.values())

# 4) Регексы для литералов/разделителей
t_OP_ASSIGN = r':='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','

# 5) Пробелы и табы игнорируем, но НЕ перевод строки
t_ignore = ' \t'


# 6) Перевод строки выдаём как токен
def t_NEWLINE(t):
    r'\r?\n'
    t.lexer.lineno += 1
    return t


# 7) Целые
def t_INT_LITERAL(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t


# 8) Идентификаторы и ключевые слова
def t_IDENTIFIER(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'IDENTIFIER')
    return t


# 9) Комментарии C++-стиля
def t_comment(t):
    r'//.*'
    pass


# 10) Ошибка
def t_error(t):
    print(f"Illegal character {t.value[0]!r} at line {t.lexer.lineno}")
    t.lexer.skip(1)


lexer = lex.lex()


def lex_types(s: str):
    lexer.input(s)
    return [tok.type for tok in lexer]


if __name__ == '__main__':
    sample = """
        compute_coords(d)
            IF (free) (
            x := nx
            y := ny
            dir := d
        )
        """
    # sample = open('program.txt').read().strip() + '\n'
    print(lex_types(sample))
