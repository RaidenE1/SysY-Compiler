import sys
from ply import lex

reserved = {
    '=' : 'Assign',
    ';' : 'Semicolon',
    '(' : 'LPar',
    ')' : 'RPar',
    '{' : 'LBrace',
    '}' : 'RBrace',
    '+' : 'Plus',
    '*' : 'Mult',
    '/' : 'Div',
    '<' : 'Lt',
    '>' : 'Gt',
    '%' : 'Mod',
    '==' : 'Eq',
    '-' : 'Minus',
    'if' : 'If',
    'else' : 'Else',
    'while' : 'While',
    'break' : 'Break',
    'continue' : 'Continue',
    'return' : 'Return',
    'main' : 'Main',
    'int' : 'Int',
    'const' : 'Const',
    ',' : 'Comma'
}

tokens = ['COMMENT', 'DECIMAL', 'OCTAL', 'HEXADECIMAL', 'RESERVED', 'IDENT'] + list(reserved.values())

def t_COMMENT(t):
     r'(//.*)|(/\*(.|\r\n|\n|\t\n)*?\*/)'
     pass

def t_RESERVED(t):
    r'[a-zA-Z_][0-9]*[a-zA-Z_]*|\{|\}|\(|\)|\+|\*|;|-|/|%|='
    if t.value in reserved.keys():
        t.type = reserved.get(t.value)# Check for reserved words
        return t
    else:
        t.type = 'IDENT'
        return t

def t_HEXADECIMAL(t):
    r'0[xX][0-9a-fA-F]+'
    t.value = int(t.value, 16)
    return t

def t_DECIMAL(t):
    r'[1-9]\d*'
    t.value = int(t.value)    
    return t

def t_OCTAL(t):
    r'0[0-7]*'
    if len(t.value) == 1:
        t.value = 0
    else:
        res = 0
        j = 1
        for i in range(len(t.value)-1, 0, -1):
            res += int(t.value[i]) * (8 ** (j-1))
            j += 1
        t.value = res
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_IGNORE(t):
    r'\s+'
    pass

def t_error(t):
    # sys.exit(1)
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)



