import sys
from ply import lex
import tokrules
from tokrules import tokens
from parser_modules import run_parser

def lexer_init(text):
    lexer = lex.lex(module = tokrules)
    lexer.input(text)
    return lexer

def print_out(result, path):
    # print(result)
    file = open(path, 'w')
    title = result[0]
    if title == 'FuncDef':
        file.write('define dso_local ')
    tok_list = result[1]
    for idx,tok in enumerate(tok_list):
        if tok == 'int':
            file.write('i32')
        elif tok == 'main':
            file.write('@main')
        elif tok == '(' or tok == ')':
            file.write(tok + ' ')
        elif tok == 'return':
            file.write('ret ')
        elif tok == ';':
            file.write('\n')
        elif tok == '{' or tok == '}':
            file.write(tok + '\n')
        elif type(tok) == int:
            file.write('i32 ' + str(tok))


def main(args):
    # print(tokens)
    input_path = args[1]
    output_path = args[2]
    text = open(input_path, 'r').read()
    # print(text)
    lexer = lexer_init(text)
    result = run_parser(text, lexer)
    print_out(result, output_path)

if __name__ == '__main__':
    main(sys.argv)
