from re import A
import sys
from ply import yacc
from tokrules import tokens
from ast_modules import AstNode

def p_CompUnit(p):
    ''' CompUnit : CompUnit FuncDef 
                 | CompUnit Decl
                 | FuncDef
                 | Decl'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2]], 'CU')

def p_FuncDef(p):
    ''' FuncDef : Int IDENT LPar FuncParams RPar Block
                | Void IDENT LPar FuncParams RPar Block
                | Int IDENT LPar RPar Block
                | Void IDENT LPar RPar Block '''
    p[0] = AstNode('NT', p[1:], 'FuncDef')

def p_FuncParams(p):
    ''' FuncParams : FuncParam AddFuncParam 
                   | FuncParam '''
    p[0] = AstNode('NT', p[1:], 'FuncPDecl')

def p_AddFuncParam(p):
    ''' AddFuncParam : Comma FuncParam AddFuncParam
                     | Comma FuncParam '''
    p[0] = AstNode('NT', p[1:], 'AddFuncParam')
    
def p_FuncParam(p):
    ''' FuncParam : Int IDENT LBracket RBracket AddBracket
                  | Int IDENT LBracket RBracket
                  | Int IDENT '''
    p[0] = AstNode('NT', p[1:], 'FuncParam')

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
    ''' ConstDecl : Const Int AddConstDef Semicolon '''
    p[0] = AstNode('NT', [p[1], p[2], p[3], p[4]], 'ConstDecl')

def p_AddConstDef(p):
    ''' AddConstDef : ConstDef Comma AddConstDef
                    | ConstDef '''
    if len(p) == 4:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'AddConstDef')
    else:
        p[0] = p[1]

def p_ConstDef(p):
    ''' ConstDef : IDENT Assign ConstInitVal 
                 | IDENT AddBracket Assign ConstInitVal'''
    if len(p) == 4:
        p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1], True), p[2], p[3]], 'ConstDef')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4]], 'ConstArr')

def p_AddBracket(p):
    ''' AddBracket : LBracket AddExp RBracket AddBracket
                   | LBracket AddExp RBracket '''
    p[0] = AstNode('NT', p[1:], 'AddBracket')

def p_ConstInitVal(p):
    ''' ConstInitVal : AddExp 
                     | LBrace RBrace 
                     | LBrace ConstInitVal RBrace 
                     | LBrace ConstInitVal AddConstInitVal RBrace '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', p[1:], 'ArrDecl')

def p_AddConstInitval(p):
    ''' AddConstInitVal : Comma ConstInitVal AddConstInitVal 
                        | Comma ConstInitVal '''
    if len(p) == 3:
        p[0] = AstNode('NT', [p[1], p[2]], 'AddConstInitVal')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'AddConstInitVal')
            
    
def p_VarDecl(p):
    ''' VarDecl : Int AddVarDef Semicolon '''
    p[0] = AstNode('NT', [p[1], p[2], p[3]], 'VarDecl')

def p_AddVarDef(p):
    ''' AddVarDef : VarDef Comma AddVarDef
                  | VarDef '''
    if len(p) == 4:
        p[0] = AstNode('AddVarDef', [p[1], p[2], p[3]], 'AddVarDef')
    else:
        p[0] = p[1]

def p_VarDef(p):
    ''' VarDef  : IDENT AddBracket Assign InitVal
                | IDENT AddBracket
                | IDENT Assign InitVal 
                | IDENT '''
    if len(p) == 2:
        p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1], False)], 'VarDef')
    elif len(p) == 3:
        p[0] = AstNode('NT', [p[1], p[2]], 'VarArr')
    elif len(p) == 4:
        p[0] = AstNode('NT', [AstNode('T', None, 'Ident', p[1], False), p[2], p[3]], 'VarDef')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4]], 'VarArr')

def p_InitVal(p):
    ''' InitVal : Exp 
                | LBrace RBrace
                | LBrace InitVal RBrace
                | LBrace InitVal AddInitVal RBrace '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', p[1:], 'InitVal')

def p_AddInitVal(p):
    ''' AddInitVal : Comma InitVal AddInitVal
                   | Comma InitVal '''
    p[0] = AstNode('NT', p[1:], 'AddInitVal')

def p_Stmt(p):
    ''' Stmt : Semicolon
             | Block
             | Exp Semicolon 
             | Continue Semicolon
             | Break Semicolon
             | Return Semicolon
             | Return Exp Semicolon 
             | LVal Assign Exp Semicolon
             | If LPar Cond RPar Stmt 
             | While LPar Cond RPar Stmt
             | If LPar Cond RPar Stmt Else Stmt '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == 'continue':
            p[0] = AstNode('NT', [p[1], p[2]], 'Cont')
        elif p[1] == 'break':
            p[0] = AstNode('NT', [p[1], p[2]], 'Break')
        elif p[1] == 'return':
            p[0] = AstNode('NT', [p[1], p[2]], 'return')
        else:
            p[0] = AstNode('NT', [p[1], p[2]], 'ExpSemi')
    elif len(p) == 4:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'return')
    elif len(p) == 5:
        p[0] = AstNode('NT', [p[1], p[2], p[3], p[4]], 'VarAssign')
    elif len(p) == 6:
        if p[1] == 'if':
            p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5]], 'IfElse')
        else:
            p[0] = AstNode('NT', [p[1], p[2], p[3], p[4], p[5]], 'While')
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
    ''' LVal : IDENT 
             | IDENT AddLVal '''
    if len(p) == 2:
        p[0] = AstNode('T', None, 'Ident', p[1], False)
    else:
        p[0] = AstNode('T', [p[1], p[2]], 'ArrVal', p[1])

def p_AddLVal(p):
    ''' AddLVal : LBracket Exp RBracket AddLVal 
                | LBracket Exp RBracket '''
    p[0] = AstNode('NT', p[1:], 'AddLVal')
        
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
                 | IDENT LPar RPar
                 | IDENT LPar FuncRParams RPar
                 | NG UnaryExp
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
    p[0] = AstNode('NT', p[1:], 'FuncRParams')

def p_Exps(p):
    ''' Exps : Comma Exp Exps
             | Comma Exp '''
    p[0] = AstNode('NT', p[1:], 'Exps')


def p_PrimaryExp(p):
    ''' PrimaryExp : LPar Exp RPar 
                   | Number 
                   | LVal '''
    p[0] = AstNode('NT', p[1:], 'PriExp')

def p_Number(p):
    ''' Number  : DECIMAL 
                | OCTAL 
                | HEXADECIMAL '''
    p[0] = AstNode('T', None, 'Number', p[1])

def p_error(p):
    print("Error de sintaxis", p)
    print("Error en linea: "+ str(p.lineno))
    sys.exit(1)

def run_parser(text, lexer):
    parser = yacc.yacc(start = 'CompUnit')
    result = parser.parse(text, lexer)
    # print(result)
    return result

