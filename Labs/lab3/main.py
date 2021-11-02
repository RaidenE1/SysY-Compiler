import sys
from ply import lex
import tokrules
from tokrules import tokens
from parser_modules import run_parser

FILE_IN = None
FILE_OUT = None

VALUE_MAP = dict()
LOC = 1

def lexer_init(text):
    lexer = lex.lex(module = tokrules)
    lexer.input(text)
    return lexer

# def print_out(result, path):
#     # print(result)
#     file = open(path, 'w')
#     title = result[0]
#     if title == 'FuncDef':
#         file.write('define dso_local ')
#     tok_list = result[1]
#     for idx,tok in enumerate(tok_list):
#         if tok == 'int':
#             file.write('i32')
#         elif tok == 'main':
#             file.write('@main')
#         elif tok == '(' or tok == ')':
#             file.write(tok + ' ')
#         elif tok == 'return':
#             file.write('ret ')
#         elif tok == ';':
#             file.write('\n')
#         elif tok == '{' or tok == '}':
#             file.write(tok + '\n')
#         elif type(tok) == int:
#             file.write('i32 ' + str(tok))

def print_node(n):
    FILE_OUT.write(str(n.val) + ' ')

def LDR(n):
    if n != None and n.type != 'T':
        print()
        print(n.name)
        print()
        if n.name == 'FuncDef':
            FILE_OUT.write('define dso_local ')
        for idx, child in enumerate(n.children):
            if type(child) == 'AstNode':
                if child.type == 'T':
                    print_node(child)
                else:
                    LDR(child)
            else:
                print('type of node is :' + type(child))

                assert type(child) == 'str'

                if child == '{' or child == '}' or child == ';':
                    FILE_OUT.write(child + '\n')
                else:
                    FILE_OUT.write(child + ' ')
        if n.name == 'VarDef':
            if len(n.children) == 3:
                VALUE_MAP[n.children[0].val] = n.children[2].val

def main(args):
    # print(tokens)
    FILE_IN = open(args[1], 'r')
    FILE_OUT = open(args[2], 'w')

    assert FILE_IN is not None
    assert FILE_OUT is not None

    text = FILE_IN.read()
    # print(text)
    lexer = lexer_init(text)
    result = run_parser(text, lexer)
    # print_out(result, output_path)
    LDR(result)

    FILE_IN.close()
    FILE_OUT.close()

if __name__ == '__main__':
    main(sys.argv)
