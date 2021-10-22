'''
Author: Asuka
Date: 2021-10-19 08:42:27
LastEditTime: 2021-10-22 23:58:17
LastEditors: Please set LastEditors
Description: parser of the compiler
FilePath: /lab2/parser_modules.py
'''
import sys
from ply import yacc
from tokrules import tokens

def p_Parser_init(p):
    ''' CompUnit : FuncDef '''
    p[0] = ['FuncDef', p[1]]
    
def p_FuncDef(p):
    ''' FuncDef : FuncType Ident LPar RPar Block'''
    p[0] = [p[1], p[2], p[3], p[4]] + p[5]

def p_FuncType(p):
    ''' FuncType : Int '''
    p[0] = p[1]

def p_Ident(p):
    ''' Ident : Main '''
    p[0] = p[1]

def p_Block(p):
    ''' Block : LBrace Stmt RBrace '''
    p[0] = [p[1]] + p[2] + [p[3]] 

def p_Stmt(p):
    ''' Stmt : Return Exp Semicolon '''
    p[0] = [p[1], int(eval(p[2])), p[3]]

def p_Exp(p):
    ''' Exp : AddExp '''
    p[0] = p[1]

def p_AddExp(p):
    ''' AddExp : MulExp 
               | AddExp Plus MulExp
               | AddExp Minus MulExp '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + ' ' + p[2] + ' ' + p[3]

def p_MulExp(p):
    ''' MulExp : UnaryExp 
               | MulExp Div UnaryExp
               | MulExp Mult UnaryExp
               | MulExp Mod UnaryExp'''
    if len(p) == 2:
        p[0] = str(p[1])
    elif p[2] == '/':
        p[0] = p[1] + ' // ' + p[3]
    elif p[2] == '%':
        if eval(p[1]) < 0: 
            p[0] = str(- (abs(eval(p[1]) % abs(eval(p[3])))))
        else:
            p[0] = str( (abs(eval(p[1]) % abs(eval(p[3])))))
    else: 
        p[0] = p[1] + ' ' + p[2] + ' ' + p[3]

def p_UnaryExp(p):
    ''' UnaryExp : PrimaryExp 
                 | Plus UnaryExp
                 | Minus UnaryExp '''
    if len(p) == 2:
        p[0] = str(p[1])
    else:
        p[0] = p[1] + ' ' + str(p[2])


def p_PrimaryExp(p):
    ''' PrimaryExp : LPar Exp RPar 
                   | Number '''
    if len(p) == 2:
        p[0] = str(p[1])
    else:
        p[0] = p[1] + ' ' + p[2] + ' ' + p[3]

def p_Number(p):
    ''' Number  : DECIMAL 
                | OCTAL 
                | HEXADECIMAL '''
    p[0] = p[1]

def p_error(p):
    sys.exit(1)
    # print("Error de sintaxis", p)
    # print("Error en linea: "+ str(p.lineno))

def run_parser(text, lexer):
    parser = yacc.yacc(start = 'CompUnit')
    result = parser.parse(text, lexer)
    # print(result)
    return result


