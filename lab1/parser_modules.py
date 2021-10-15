import sys
from ply import yacc
from tokrules import tokens

def p_Parser_init(p):
    ''' CompUnit : FuncDef '''
    # p[0] = ['FuncDef', p[1]]
    

def p_FuncDef(p):
    ''' FuncDef : FuncType Ident LPar RPar Block'''
    # p[0] = [p[1], p[2], p[3], p[4], p[5]]

def p_FuncType(p):
    ''' FuncType : Int '''
    # p[0] = [p[1], p.lineno(1)]

def p_Ident(p):
    ''' Ident : Main '''
    # p[0] = [p[1], p.lineno(1)]

def p_Block(p):
    ''' Block : LBrace Stmt RBrace '''
    # p[0] = [[p[1], p.lineno(1)], p[2], [p[3], p.lineno(3)]]  

def p_Stmt(p):
    ''' Stmt : Return Number Semicolon '''
    # p[0] = [[p[1], p.lineno(1)], [p[2], p.lineno(2)], [p[3], p.lineno(3)]]

def p_Number(p):
    ''' Number  : DECIMAL 
                | OCTAL 
                | HEXADECIMAL '''
    # p[0] = [p[1], p.lineno(1)]

def p_error(p):
    sys.exit(1)
    # print("Error de sintaxis", p)
    # print("Error en linea: "+ str(p.lineno))

def run_parser(text, lexer):
    parser = yacc.yacc(start = 'CompUnit')
    result = parser.parse(text, lexer)

