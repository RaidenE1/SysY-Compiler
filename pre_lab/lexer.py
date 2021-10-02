'''
Author: your name
Date: 2021-09-27 23:16:50
LastEditTime: 2021-09-28 12:48:05
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /SysY-programming-language/pre/main.py
'''
import sys


def checkNum(d):
    if d >= '0' and d <= '9':
        return True

def checkLetter(l):
    if (l >= 'a' and l <= 'z') or (l >= 'A' and l <= 'Z'):
        return True
    else:
        return False

def checkIdentifier(i):
    

def checkToken(t):
    identifiers = {
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
        '==' : 'Eq',
        'if' : 'If',
        'else' : 'Else',
        'while' : 'While',
        'break' : 'Break',
        'continue' : 'Continue',
        'return' : 'Return'
    }

def textExcuter(line):
    for char in line:
        
        
def main(argv):
    path = argv[-1]
    print(path)
    f = open(path, 'r')
    for line in f:
        textExcuter(line)


if __name__ == "__main__":
    main(sys.argv)