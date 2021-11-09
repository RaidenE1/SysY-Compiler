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

def check_val(n):
    if isinstance(n, AstNode):
        if n.type == 'T':
            if n.name == 'Ident':
                if not VALUE_MAP[n.val].const:
                    return True
                else:
                    return False
            else:
                return False
        else:
            flag = False
            for child in n.children:
                flag = flag or check_val(child)
            return flag
    else:
        return False

def operate_exp(n):
    global VALUE_MAP
    global FILE_OUT
    global LOC
    assert n.name[-3:] == 'Exp'
    if n.name == 'PriExp':
        if len(n.children) == 1:
            res = n.children[0]
            if res.name == 'Number':
                return res.val, False
            elif res.name == 'Ident':
                if res.val not in VALUE_MAP.keys():
                    exit(1)
                LOC += 1
                FILE_OUT.write('%%x%d = load i32, i32* %%x%d\n' % (LOC - 1, VALUE_MAP[res.val].loc))
                # print('pri load')
                return '%x' + str(LOC - 1), False
            else:
                print("not int not str")
        else: 
            return operate_exp(n.children[1])
    elif n.name == 'UnaryExp':
        if len(n.children) == 2:
            op = n.children[0]
            if op == '+':
                res = operate_exp(n.children[1])
                if isinstance(res[0], int):
                    return res[0], False
                elif isinstance(res[0], str):
                    if res[1]:
                        # print(res[0])
                        FILE_OUT.write("%%x%d = load i32, i32* " % (LOC))
                        FILE_OUT.write(res[0] + '\n')
                        LOC += 1
                    # print('+load')
                    return '%x' + str(LOC - 1), False
            elif op == '-':
                res = operate_exp(n.children[1])
                if isinstance(res[0], int):
                    return -res[0], False
                elif isinstance(res[0], str):
                    if res[1]:
                        FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res[0]))
                        LOC += 1
                    # print('-load')
                    FILE_OUT.write("%%x%d = mul i32 %d, " % (LOC, -1))
                    FILE_OUT.write(res[0] + '\n')
                    LOC += 1
                    return '%x' + str(LOC - 1), False
            elif op == '!':
                res = operate_exp(n.children[1])
                loc = res[0]
                if res[1]:
                    FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res[0]))
                    LOC += 1
                    loc = '%x' + str(LOC - 1)
                # print('-load')
                # FILE_OUT.write('%%x%d = zext i1 %s to i32\n' %(LOC, loc))
                # LOC += 1
                FILE_OUT.write("%%x%d = icmp eq i32 %%x%d, 0\n" % (LOC, LOC - 1))
                LOC += 1
                FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
                LOC += 1
                return '%x' + str(LOC - 1), False
        else:
            print("UnaryExp Error")
    elif n.name == 'SysFuncExp':
        if len(n.children) == 4:
            param = operate_exp(n.children[2])
            if n.children[0] == 'putint':
                FILE_OUT.write("call void @putint(i32 %s)\n" %(param[0]))
            elif n.children[0] == 'putch':
                FILE_OUT.write("call void @putch(i32 %s)\n" %(param[0]))
            else:
                print('SysFuncOP Error')
                exit(0)
        elif len(n.children) == 3:
            if n.children[0] == 'getint':
                FILE_OUT.write("%%x%d = call i32 @getint()\n" % (LOC))
                LOC += 1
                return '%x' + str(LOC - 1), False
            elif n.children[0] == 'getch':
                FILE_OUT.write("%x%d = call i32 @getch()\n" %(LOC))
                LOC += 1
                return '%x' + str(LOC - 1), False
            else:
                print('SysFuncOP Error 3')
                exit(0)
        else:
            print('SysFunc Error')
            exit(0)
    elif n.name == 'MulExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])
            op2 = operate_exp(n.children[2])
            if n.children[1] == '//':
                if isinstance(op1[0], str) or isinstance(op2[0], str):
                    FILE_OUT.write("%%x%d = sdiv i32 %s, %s\n" %(LOC, str(op1[0]), str(op2[0])))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(op1[0]) + ' // ' + str(op2[0]))), False
            elif n.children[1] == '*':
                if isinstance(op1[0], str) or isinstance(op2[0], str):
                    FILE_OUT.write("%%x%d = mul i32 %s, %s\n" %(LOC, str(op1[0]), str(op2[0])))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(op1[0]) + ' * ' + str(op2[0]))), False
            elif n.children[1] == '%':
                if isinstance(op1[0], str) or isinstance(op2[0], str):
                    FILE_OUT.write("%%x%d = srem i32 %s, %s\n" %(LOC, str(op1[0]), str(op2[0])))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    if op1 >= 0 :
                        sign = 1
                    else:
                        sign = -1
                    return sign * int(eval(str(abs(op1[0])) + ' % ' + str(abs(op2[0])))), False
            else:
                print('MulExp OP Error')
                exit(1)
    elif n.name == 'AddExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])
            op2 = operate_exp(n.children[2])
            if n.children[1] == '+':
                if isinstance(op1[0], str) or isinstance(op2[0], str):
                    FILE_OUT.write("%%x%d = add i32 %s, %s\n" %(LOC, str(op1[0]), str(op2[0])))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(op1[0]) + ' + ' + str(op2[0]))), False
            elif n.children[1] == '-':
                if isinstance(op1[0], str) or isinstance(op2[0], str):
                    FILE_OUT.write("%%x%d = sub i32 %s, %s\n" %(LOC, str(op1[0]), str(op2[0])))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(op1[0]) + ' - ' + str(op2[0]))), False
            else:
                print('AddExp OP Error')
                exit(1)
    elif n.name == 'RelExp':
        OpMap = {
            '<' : 'slt',
            '<=' : 'sle',
            '>' : 'sgt',
            '>=' : 'sge'
        }
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])[0]
            op2 = operate_exp(n.children[2])[0]
            op = OpMap.get(n.children[1], None)
            assert op is not None
            FILE_OUT.write('%%x%d = icmp %s i32 %s, %s\n' % (LOC, op, op1, op2))
            LOC += 1
            FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('RelExp len Error')
            exit(1)
    elif n.name == 'EqExp':
        OpMap = {
            '==' : 'eq',
            '!=' : 'ne',
        }
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])[0]
            op2 = operate_exp(n.children[2])[0]
            op = OpMap.get(n.children[1], None)
            assert op is not None
            FILE_OUT.write('%%x%d = icmp %s i32 %s, %s\n' % (LOC, op, op1, op2))
            LOC += 1
            FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('EqExp len Error')
            exit(1)
    elif n.name == 'LAndExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])[0]
            op2 = operate_exp(n.children[2])[0]
            FILE_OUT.write('%%x%d = and i32 %s, %s\n' % (LOC, op1, op2))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('LAndExp len Error')
            exit(1)
    elif n.name == 'LOrExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])[0]
            op2 = operate_exp(n.children[2])[0]
            FILE_OUT.write('%%x%d = or i32 %s, %s\n' % (LOC, op1, op2))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('LAndExp len Error')
            exit(1)
    else:
        print('EXP OPERATION ERROR')
        exit(1)

def if_else_operator(n):
    global FILE_OUT
    global LOC
    loc_after = 0
    assert n.name == 'IfElse'
    if len(n.children) == 5:
        res = operate_exp(n.children[2])
        FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0]))
        loc0 = LOC
        LOC += 1
        stmt = n.children[4]
        LOC += 2
        loc = LOC - 2
        loc_after = LOC - 1
        FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(loc0, loc, loc_after))     
        block_operate(stmt, loc, loc_after)
        # FILE_OUT.write('br label %%x%d\n' %(loc))
    elif len(n.children) == 7:
        res = operate_exp(n.children[2])
        FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0]))
        loc0 = LOC
        LOC += 1
        stmt1 = n.children[4]
        stmt2 = n.children[6]
        LOC += 3
        loc1 = LOC - 3
        loc2 = LOC - 2
        loc_after = LOC - 1
        FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(loc0, loc1, loc2))
        block_operate(stmt1, loc1, loc_after)
        # FILE_OUT.write('br label %%x%d\n' %(loc2))
        block_operate(stmt2, loc2, loc_after)
    else:
        print('IfElse len Error')
        sys.exit()
    FILE_OUT.write('x%d:\n'%(loc_after))

def block_operate(n, loc, loc_after):
    global FILE_OUT
    global LOC 
    FILE_OUT.write('x%d:\n' % (loc))
    if n.name == 'IfElse':
        if_else_operator(n)
    else:
        LDR(n, True)
    FILE_OUT.write('br label %%x%d\n' % (loc_after))
    

                
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

def LDR(n, ignore = False):
    if n != None and n.type != 'T':
        global FILE_OUT
        global VALUE_MAP
        global LOC
        # print(n.name)
        if n.name == 'FuncDef':
            FILE_OUT.write('define dso_local ')
        elif n.name == 'VarDef':
            var = n.children[0]
            # print(var.val)
            assert var.name == 'Ident'
            if len(n.children) == 3:
                if var.val in VALUE_MAP.keys():
                    old_node = VALUE_MAP[var.val]
                else:
                    var.loc = LOC 
                    LOC += 1
                    VALUE_MAP[var.val] = var
                    FILE_OUT.write('%%x%d = alloca i32\n' % (var.loc))
                res = operate_exp(n.children[2])[0]
                FILE_OUT.write('store i32 %s, i32* %%x%d ' %(str(res), VALUE_MAP[var.val].loc))
            else:
                var.loc = LOC
                LOC += 1
                VALUE_MAP[var.val] = var
                FILE_OUT.write('%%x%d = alloca i32\n' % (var.loc))
            return
        elif n.name == 'ConstDef':
            var = n.children[0]
            var.loc = LOC 
            LOC += 1
            VALUE_MAP[var.val] = var
            FILE_OUT.write('%%x%d = alloca i32\n' % (var.loc))
            if check_val(n.children[2]):
                sys.exit(1)
            res = operate_exp(n.children[2])[0]
            FILE_OUT.write('store i32 %s, i32* %%x%d' %(str(res),var.loc))
            return 
        elif n.name == 'VarAssign':
            var = n.children[0]
            assert var.name == 'Ident'
            if var.val in VALUE_MAP.keys():
                old_node = VALUE_MAP[var.val]
                if old_node.const == True:
                    sys.exit(1)
                else:
                    res = operate_exp(n.children[2])[0]
                    FILE_OUT.write('store i32 %s, i32* %%x%d \n' %(str(res), old_node.loc))
            else:
                sys.exit(1)
            return 
        elif n.name == 'return':
            op = operate_exp(n.children[1])
            FILE_OUT.write('ret i32 ' + str(op[0]) + '\n')
            return 
        elif n.name == 'IfElse':
            if_else_operator(n)
            return 
        elif n.name[-3:] == 'Exp':
            operate_exp(n)
            return

        for idx, child in enumerate(n.children):
            if isinstance(child, AstNode):
                if child.type == 'T':
                    print_node(child)
                else:
                    LDR(child)
            else:
                if child == '{' or child == '}':
                    if ignore:
                        continue
                    else:
                        FILE_OUT.write(child + '\n')
                elif child == ';' or child == ',':
                    FILE_OUT.write('\n')
                elif child == 'int':
                    FILE_OUT.write('i32 ')
                elif child == 'main':
                    FILE_OUT.write('@main ')
                elif child == 'return':
                    FILE_OUT.write('ret i32 ')
                elif child == 'const':
                    continue
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
    FILE_OUT.write("declare i32 @getch()\ndeclare void @putch(i32)\ndeclare i32 @getint()\ndeclare void @putint(i32)\n")
    lexer = lexer_init(text)
    print(text)
    # tok = lexer.token()
    # while tok:
    #     print(tok)
    #     tok = lexer.token()
    result = run_parser(text, lexer)
    # print_out(result, output_path)
    LDR(result)

    FILE_IN.close()
    FILE_OUT.close()

if __name__ == '__main__':
    main(sys.argv)
