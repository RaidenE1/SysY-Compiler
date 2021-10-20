import sys
from ply import lex
import tokrules
from tokrules import tokens
from parser_modules import run_parser

def lexer_init(text):
    lexer = lex.lex(module = tokrules)
    lexer.input(text)
    return lexer

def print_out(lexer, path):
    file = open(path, 'w')
    tok = lexer.token()
    ln = tok.lineno
    if tok:
        file.write("define dso_local ")
    while tok:
        if tok.lineno > ln:
            file.write('\n')
            ln  = tok.lineno
        if tok.value == 'int':
            file.write("i32 ")
        elif tok.value == 'main':
            file.write("@main ")
        elif tok.value == '{' or tok.value == '}' or tok.type == 'LPar' or tok.type == 'RPar' or tok.type == 'DECIMAL' or tok.type == 'HEXADECIMAL' or tok.type == 'OCTAL':
            file.write(str(tok.value))
            file.write(' ')
        elif tok.type == 'Return':
            file.write('ret i32 ')
        tok = lexer.token()

def main(args):
    input_path = args[1]
    output_path = args[2]
    text = open(input_path, 'r').read()
    lexer = lexer_init(text)
    lexer_copy = lexer.clone()
    # while True:
    #     tok = lexer.token()
    #     if not tok:
    #         break
    #     print(tok)
    run_parser(text, lexer)
    print_out(lexer_copy, output_path)

if __name__ == '__main__':
    main(sys.argv)
