from re import A
import sys
from ply import yacc
from tokrules import tokens
from ast import AstNode

def p_Parser_init(p):
    ''' CompUnit : FuncDef '''
    p[0] = AstNode('CompUnit', [p[1]])

def p_Decl(p):
    ''' Decl : ConstDecl 
             | VarDecl'''
    p[0] = AstNode('Decl', [p[1]])

def p_ConstDecl(p):
    ''' ConstDecl : Const BType ConstDef AddConstDef LBrace Comma ConstDef RBrace Semicolon '''
    p[0] = AstNode('ConstDecl', [p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8]])

def p_ConstDef(p):
    ''' ConstDef : IDENT Assign ConstInitVal '''
    p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1]), p[2], p[3]], 'ConstDef')

def p_AddConstDef(p):
    ''' AddConstDef : Comma ConstDef AddConstDef
                    | Comma ConstDef '''
    if len(p) == 4:
        p[0] = AstNode('AddConstDef', [p[1], p[2], p[3]])
    else:
        p[0] = AstNode('AddConstDef', [p[1], p[2]])

def p_BType(p):
    ''' BType : Int'''
    p[0] = AstNode('T', None, 'BType', p[1])

def p_ConstInitVal(p):
    ''' ConstInitVal : ConstExp '''
    p[0] = p[1]

def p_ConstExp(p):
    ''' ConstExp : AddExp '''
    p[0] = p[1]
    
def p_VarDecl(p):
    ''' VarDecl : BType VarDef AddVarDef Semicolon '''
    p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5], p[6], p[7]], 'VarDecl')

def p_VarDef(p):
    ''' VarDef  : IDENT
                | IDENT Assign InitVal '''
    if len(p) == 2:
        p[0] = AstNode('T', None, 'Ident', p[1])
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'VarDef')

def p_AddVarDef(p):
    ''' AddVarDef : Comma VarDef AddVarDef
                  | Comma VarDef '''
    if len(p) == 4:
        p[0] = AstNode('AddVarDef', [p[1], p[2], p[3]])
    else:
        p[0] = AstNode('AddVarDef', [p[1], p[2]])


def p_InitVal(p):
    ''' InitVal : Exp '''
    p[0] = p[1]

def p_FuncDef(p):
    ''' FuncDef : FuncType Main LPar RPar Block'''
    p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5]])

def p_FuncType(p):
    ''' FuncType : Int '''
    p[0] = AstNode('T', None, 'FuncType', p[1])

def p_Block(p):
    ''' Block : LBrace BlockItem AddBlock RBrace '''
    if p[3] == None:
        p[0] = AstNode('Block', [p[1], p[2], p[4]])
    else:
        p[0] = AstNode('Block', [p[1], p[2], p[3], p[4]])

def p_BlockItem(p):
    ''' BlockItem : Decl 
                  | Stmt '''
    p[0] = AstNode('BlockItem', [p[1]])

def p_AddBlock(p):
    ''' AddBlock : BlockItem
                 | empty'''
    p[0] = p[1]

def p_Stmt(p):
    ''' Stmt : Return Exp Semicolon 
             | LVal Assign Exp Semicolon
             | Exp Semicolon '''
    if len(p) == 4:
        p[0] = AstNode('Stmt', [p[1], p[2], p[3]])
    elif len(p) == 5:
        p[0] = AstNode('Assign', [p[1], p[2], p[3], p[4]])
    else:
        p[0] = AstNode('Stmt', [p[1], p[2]])

def p_LVal(p):
    ''' LVal : IDENT '''
    p[0] = AstNode('T', None, 'Ident', p[1])
     
def p_Exp(p):
    ''' Exp : AddExp '''
    p[0] = p[1]

def p_AddExp(p):
    ''' AddExp : MulExp 
               | AddExp Plus MulExp
               | AddExp Minus MulExp '''
    if len(p) == 2:
        res_val = p[1].val
    else:
        res_val = p[1].val + ' ' + p[2] + ' ' + p[3].val
    p[0] = AstNode('T', None, 'AddExp', int(eval(res_val)))

def p_MulExp(p):
    ''' MulExp : UnaryExp 
               | MulExp Div UnaryExp
               | MulExp Mult UnaryExp
               | MulExp Mod UnaryExp'''
    if len(p) == 2:
        res_val = str(p[1])
    elif p[2] == '/':
        res_val = p[1] + ' // ' + p[3]
    elif p[2] == '%':
        if eval(p[1]) < 0: 
            res_val = str(- (abs(eval(p[1]) % abs(eval(p[3])))))
        else:
            res_val = str( (abs(eval(p[1]) % abs(eval(p[3])))))
    else: 
        res_val = p[1] + ' ' + p[2] + ' ' + p[3]
    p[0] = AstNode('T', None, 'MulExp', int(eval(res_val)))

def p_UnaryExp(p):
    ''' UnaryExp : PrimaryExp 
                 | Plus UnaryExp
                 | Minus UnaryExp '''
    if len(p) == 2:
        res_val = str(p[1].val)
    else:
        res_val = str(p[1].val) + ' ' + str(p[2].val)
    p[0] = AstNode('T', None, 'UnaryExp', int(eval(res_val)))


def p_PrimaryExp(p):
    ''' PrimaryExp : LPar Exp RPar 
                   | Number 
                   | LVal '''
    if len(p) == 2:
        res_val = str(p[1].val)
    else:
        res_val = str(p[1].val) + ' ' + str(p[2].val) + ' ' + str(p[3].val)
    p[0] = AstNode('T', None, 'PriExp', int(eval(res_val)))

def p_Number(p):
    ''' Number  : DECIMAL 
                | OCTAL 
                | HEXADECIMAL '''
    res_val = str(p[1])
    p[0] = AstNode('T', None, 'Number', int(eval(res_val)))

def p_error(p):
    # sys.exit(1)
    print("Error de sintaxis", p)
    print("Error en linea: "+ str(p.lineno))

def run_parser(text, lexer):
    parser = yacc.yacc(start = 'CompUnit')
    result = parser.parse(text, lexer)
    # print(result)
    return result


