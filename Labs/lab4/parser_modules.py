from re import A
import sys
from ply import yacc
from tokrules import tokens
from ast_modules import AstNode

def p_CompUnit(p):
    ''' CompUnit : FuncDef '''
    p[0] = p[1]

def p_FuncDef(p):
    ''' FuncDef : FuncType Main LPar RPar Block'''
    p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5]], 'FuncDef')

def p_FuncType(p):
    ''' FuncType : Int '''
    p[0] = p[1]

def p_Block(p):
    ''' Block : LBrace AddBlock RBrace '''
    p[0] = AstNode('NT', [p[1], p[2], p[3]], 'Block')

def p_AddBlock(p):
    ''' AddBlock : BlockItem 
                 | BlockItem AddBlock'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2]], 'AddBlock')

def p_BlockItem(p):
    ''' BlockItem : Decl 
                  | Stmt '''
    p[0] = p[1]

def p_Decl(p):
    ''' Decl : ConstDecl 
             | VarDecl'''
    p[0] = p[1]

def p_ConstDecl(p):
    ''' ConstDecl : Const BType AddConstDef Semicolon '''
    p[0] = AstNode('ConstDecl', [p[1], p[2], p[3], p[4]], 'ConstDecl')

def p_AddConstDef(p):
    ''' AddConstDef : ConstDef Comma AddConstDef
                    | ConstDef '''
    if len(p) == 4:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'AddConstDef')
    else:
        p[0] = p[1]

def p_ConstDef(p):
    ''' ConstDef : IDENT Assign ConstInitVal '''
    p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1], True), p[2], p[3]], 'ConstDef')

def p_BType(p):
    ''' BType : Int'''
    p[0] = AstNode('T', None, 'BType', p[1])

def p_ConstInitVal(p):
    ''' ConstInitVal : AddExp '''
    p[0] = p[1]

# def p_ConstExp(p):
#     ''' ConstExp : AddExp '''
#     p[0] = p[1]
    
def p_VarDecl(p):
    ''' VarDecl : BType AddVarDef Semicolon '''
    p[0] = AstNode('NT', [p[1], p[2], p[3]], 'VarDecl')

def p_AddVarDef(p):
    ''' AddVarDef : VarDef Comma AddVarDef
                  | VarDef '''
    if len(p) == 4:
        p[0] = AstNode('AddVarDef', [p[1], p[2], p[3]], 'AddVarDef')
    else:
        p[0] = p[1]

def p_VarDef(p):
    ''' VarDef  : IDENT
                | IDENT Assign InitVal '''
    if len(p) == 2:
        p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1], False)], 'VarDef')
    else:
        p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1], False), p[2], p[3]], 'VarDef')

def p_InitVal(p):
    ''' InitVal : Exp '''
    p[0] = p[1]

def p_Stmt(p):
    ''' Stmt : Semicolon
             | Block
             | Exp Semicolon 
             | Return Exp Semicolon 
             | LVal Assign Exp Semicolon
             | If LPar Cond RPar Stmt 
             | If LPar Cond RPar Stmt Else Stmt '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = AstNode('NT', [p[1], p[2]], 'ExpSemi')
    elif len(p) == 4:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'return')
    elif len(p) == 5:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4]], 'VarAssign')
    elif len(p) == 6:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5]], 'IfElse')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5], p[6], p[7]], 'IfElse')

def p_Cond(p):
    ''' Cond : LOrExp '''
    p[0] = p[1]

def p_LOrExp(p):
    ''' LOrExp : LAndExp
               | LOrExp OR LAndExp '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'LOrExp')

def p_LAndExp(p):
    ''' LAndExp : EqExp
                | LAndExp AND EqExp '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'LAndExp')

def p_EqExp(p):
    ''' EqExp : RelExp
              | EqExp Eq RelExp 
              | EqExp NotEq RelExp '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'EqExp')

def p_RelExp(p):
    ''' RelExp : AddExp
               | RelExp Lt AddExp
               | RelExp Gt AddExp
               | RelExp Le AddExp
               | RelExp Ge AddExp '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'RelExp')
    
def p_LVal(p):
    ''' LVal : IDENT '''
    p[0] = AstNode('T', None, 'Ident', p[1], False)
     
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
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'AddExp')

def p_MulExp(p):
    ''' MulExp : UnaryExp 
               | MulExp Div UnaryExp
               | MulExp Mult UnaryExp
               | MulExp Mod UnaryExp'''
    if len(p) == 2:
        p[0] = p[1]
    elif p[2] == '/':
        p[0] = AstNode('NT', [p[1], '//', p[3]], 'MulExp')
    else: 
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'MulExp')

def p_UnaryExp(p):
    ''' UnaryExp : PrimaryExp 
                 | Plus UnaryExp
                 | Minus UnaryExp 
                 | SysFunc LPar RPar
                 | SysFunc LPar FuncRParams RPar '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = AstNode('NT', [p[1], p[2]], 'UnaryExp')
    elif len(p) == 4:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'SysFuncExp')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4]], 'SysFuncExp')

def p_FuncRParams(p):
    ''' FuncRParams : Exp Exps
                    | Exp '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2]], 'FuncRParams')

def p_Exps(p):
    ''' Exps : Comma Exp '''
    p[0] = AstNode('NT', [p[1], p[2]], 'Exps')


def p_PrimaryExp(p):
    ''' PrimaryExp : LPar Exp RPar 
                   | Number 
                   | LVal '''
    if len(p) == 2:
        p[0] = AstNode('NT', [p[1]], 'PriExp')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'PriExp')

def p_Number(p):
    ''' Number  : DECIMAL 
                | OCTAL 
                | HEXADECIMAL '''
    p[0] = AstNode('T', None, 'Number', p[1])

def p_error(p):
    sys.exit(1)
    # print("Error de sintaxis", p)
    # print(p.value)
    # print("Error en linea: "+ str(p.lineno))

def run_parser(text, lexer):
    parser = yacc.yacc(start = 'CompUnit')
    result = parser.parse(text, lexer)
    # print(result)
    return result


