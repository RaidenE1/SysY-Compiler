import sys
from ply import lex
import tokrules
from tokrules import tokens
from parser_modules import run_parser
from ast_modules import AstNode

FILE_IN = None
FILE_OUT = None

VALUE_MAP = dict()
LOC = 1

def lexer_init(text):
    lexer = lex.lex(module = tokrules)
    lexer.input(text)
    return lexer

def print_node(n):
    global FILE_OUT
    global VALUE_MAP
    if isinstance(n.val, int):
        FILE_OUT.write('i32 ' + str(n.val) + ' ')
    elif n.name == 'Ident':
        FILE_OUT.write('%%%d' % (n.loc))
    elif n.val == 'int':
        return 
    else:
        FILE_OUT.write(str(n.val) + ' ')

def LDR(n):
    if n != None and n.type != 'T':
        global FILE_IN
        global FILE_OUT
        global VALUE_MAP
        global LOC
        if n.name == 'FuncDef':
            FILE_OUT.write('define dso_local ')
        elif n.name == 'VarDef':
            var = n.children[0]
            assert var.name == 'Ident'
            if len(n.children) == 3:
                if var.val in VALUE_MAP.keys():
                    old_node = VALUE_MAP[var.val]
                else:
                    var.loc = LOC 
                    LOC += 1
                    VALUE_MAP[var.val] = var
                    FILE_OUT.write('%%%d = alloca i32\n' % (var.loc))
                FILE_OUT.write('store i32 %d, i32* %%%d ' %(n.children[2].val, VALUE_MAP[var.val].loc))
            else:
                var.loc = LOC
                LOC += 1
                VALUE_MAP[var.val] = var
                FILE_OUT.write('%%%d = alloca i32\n' % (var.loc))
            return
        elif n.name == 'ConstDef':
            var = n.children[0]
            var.loc = LOC 
            LOC += 1
            VALUE_MAP[var.val] = var
            FILE_OUT.write('%%%d = alloca i32\n' % (var.loc))
            FILE_OUT.write('store i32 %d, i32* %%%d' %(n.children[2].val,var.loc))
        elif n.name == 'VarAssign':
            var = n.children[0]
            assert var.name == 'Ident'
            if var.val in VALUE_MAP.keys():
                old_node = VALUE_MAP[var.val]
                if old_node.const == True:
                    exit(1)
                else:
                    FILE_OUT.write('store i32 %d, i32* %%%d ' %(n.children[3].val, old_node.loc))
            else:
                exit(1)

        for idx, child in enumerate(n.children):
            if isinstance(child, AstNode):
                if child.type == 'T':
                    print_node(child)
                else:
                    LDR(child)
            else:
                if child == '{' or child == '}':
                    FILE_OUT.write(child + '\n')
                elif child == ';':
                    FILE_OUT.write('\n')
                elif child == 'int':
                    FILE_OUT.write('i32 ')
                elif child == 'main':
                    FILE_OUT.write('@main ')
                elif child == 'return':
                    FILE_OUT.write('ret ')
                else:
                    FILE_OUT.write(child + ' ')

def main(args):
    # print(tokens)
    global FILE_IN
    global FILE_OUT
    FILE_IN = open(args[1], 'r')
    FILE_OUT = open(args[2], 'w')

    assert FILE_IN is not None
    assert FILE_OUT is not None

    text = FILE_IN.read()
    lexer = lexer_init(text)
    # print(text)
    result = run_parser(text, lexer)
    # print_out(result, output_path)
    LDR(result)

    FILE_IN.close()
    FILE_OUT.close()

if __name__ == '__main__':
    main(sys.argv)
