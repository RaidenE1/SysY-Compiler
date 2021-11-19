import sys
from ply import lex
import tokrules
from tokrules import tokens
from parser_modules import run_parser
from ast_modules import *

FILE_IN = None
FILE_OUT = None

LOC = 1
GLOBAL_LOC = 1
DOMAIN_LOC = 1

def lexer_init(text):
    lexer = lex.lex(module = tokrules)
    lexer.input(text)
    return lexer

def find_var_in_domain(domain, name):
    if not domain:
        return None
    for idx, item in enumerate(domain.item_tab):
        if item.name == name:
            return item
    return None

def find_var_cross_domain(domain, name):
    while domain:
        item = find_var_in_domain(domain, name)
        if item:
            return item
        else:
            domain = domain.father
    return None

def check_val(n, domain):
    if isinstance(n, AstNode):
        if n.type == 'T':
            if n.name == 'Ident':
                item = find_var_cross_domain(domain, n.val)
                if (not item) or item._type == 'Var':
                    sys.exit(1)
        else:
            for child in n.children:
                check_val(child, domain)

def operate_exp(n, cur_domain, glob = False):
    global VALUE_MAP
    global FILE_OUT
    global LOC
    assert n.name[-3:] == 'Exp'
    if n.name == 'PriExp':
        if len(n.children) == 1:
            var = n.children[0]
            if var.name == 'Number':
                return var.val, False
            elif var.name == 'Ident':
                item = find_var_cross_domain(cur_domain, var.val)
                if not item:
                    sys.exit(1)
                if glob:
                    return item.val, False
                LOC += 1
                FILE_OUT.write('%%x%d = load i32, i32* %s\n' % (LOC - 1, item.loc))
                return '%x' + str(LOC - 1), False
            else:
                print("not int not str")
        else: 
            return operate_exp(n.children[1], cur_domain, glob)
    elif n.name == 'UnaryExp':
        if len(n.children) == 2:
            op = n.children[0]
            if op == '+':
                res = operate_exp(n.children[1], cur_domain, glob)
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
                res = operate_exp(n.children[1], cur_domain, glob)
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
                res = operate_exp(n.children[1], cur_domain, glob)
                loc = res[0]
                if res[1]:
                    FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res[0]))
                    LOC += 1
                    loc = '%x' + str(LOC - 1)
                FILE_OUT.write("%%x%d = icmp eq i32 %%x%d, 0\n" % (LOC, LOC - 1))
                LOC += 1
                FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
                LOC += 1
                return '%x' + str(LOC - 1), False
        else:
            print("UnaryExp Error")
    elif n.name == 'SysFuncExp':
        if len(n.children) == 4:
            param = operate_exp(n.children[2], cur_domain, glob)
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
                FILE_OUT.write("%%x%d = call i32 @getch()\n" %(LOC))
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
            op1 = operate_exp(n.children[0], cur_domain, glob)
            op2 = operate_exp(n.children[2], cur_domain, glob)
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
            op1 = operate_exp(n.children[0], cur_domain, glob)
            op2 = operate_exp(n.children[2], cur_domain, glob)
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
            op1 = operate_exp(n.children[0], cur_domain, glob)[0]
            op2 = operate_exp(n.children[2], cur_domain, glob)[0]
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
            op1 = operate_exp(n.children[0], cur_domain, glob)[0]
            op2 = operate_exp(n.children[2], cur_domain, glob)[0]
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
            op1 = operate_exp(n.children[0], cur_domain)[0]
            op2 = operate_exp(n.children[2], cur_domain)[0]
            FILE_OUT.write('%%x%d = and i32 %s, %s\n' % (LOC, op1, op2))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('LAndExp len Error')
            exit(1)
    elif n.name == 'LOrExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0], cur_domain)[0]
            op2 = operate_exp(n.children[2], cur_domain)[0]
            FILE_OUT.write('%%x%d = or i32 %s, %s\n' % (LOC, op1, op2))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('LAndExp len Error')
            exit(1)
    else:
        print('EXP OPERATION ERROR')
        exit(1)

def if_else_operator(n, cur_domain, condition = None, loc_break = None, loc_continue = None):
    global FILE_OUT
    global LOC
    loc_after = 0
    assert n.name == 'IfElse'
    if len(n.children) == 5:
        res = operate_exp(n.children[2], cur_domain)
        FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0]))
        loc0 = LOC
        LOC += 1
        stmt = n.children[4]
        LOC += 2
        loc = LOC - 2
        loc_after = LOC - 1
        FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(loc0, loc, loc_after))     
        block_operate(stmt, loc, loc_after, cur_domain, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
        # FILE_OUT.write('br label %%x%d\n' %(loc))
    elif len(n.children) == 7:
        res = operate_exp(n.children[2], cur_domain)
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
        block_operate(stmt1, loc1, loc_after, cur_domain, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
        # FILE_OUT.write('br label %%x%d\n' %(loc2))
        block_operate(stmt2, loc2, loc_after, cur_domain, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
    else:
        print('IfElse len Error')
        sys.exit()
    FILE_OUT.write('x%d:\n'%(loc_after))

def block_operate(n, loc, loc_after, cur_domain, cond = None, condition = None, loc_break = None, loc_continue = None):
    global FILE_OUT
    global LOC 
    global DOMAIN_LOC
    FILE_OUT.write('x%d:\n' % (loc))
    domain = Domain(DOMAIN_LOC, children = None, father = cur_domain)
    cur_domain.children.append(domain)
    if not isinstance(n, AstNode):
        print_node(n, False)
        FILE_OUT.write('br label %%x%d\n' % (loc_after))
        return
    else:
        LDR(n, True, domain, glob = False, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
    if not cond:
        FILE_OUT.write('br label %%x%d\n' % (loc_after)) 
    else:
        res = operate_exp(cond, cur_domain)
        FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0]))
        LOC += 1
        FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc, loc_after))

def while_operate(n, cur_domain):
    global FILE_OUT
    global LOC
    global DOMAIN_LOC
    cond = n.children[2]
    stmt = n.children[4]
    LOC += 2
    loc = LOC - 2
    loc_after = LOC - 1
    res = operate_exp(cond, cur_domain)
    FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0]))
    LOC += 1
    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc, loc_after))
    block_operate(stmt, loc, loc_after, cur_domain, cond, cond, loc_after, loc)
    FILE_OUT.write('x%d:\n'%(loc_after))

def print_node(child, ignore):
    global FILE_OUT
    if child == '{' or child == '}':
        if ignore:
            pass
        else:
            FILE_OUT.write(child + '\n')
    elif child == ';' or child == ',':
        FILE_OUT.write('\n')
    elif child == 'int':
        if ignore:
            pass
        else:
            FILE_OUT.write('i32 ')
    elif child == 'main':
        FILE_OUT.write('@main ')
    elif child == 'return':
        FILE_OUT.write('ret i32 ')
    elif child == 'const':
        pass
    else:
        FILE_OUT.write(child + ' ')

def LDR(n, ignore = False, cur_domain = None, glob = False, condition = None, loc_break = None, loc_continue = None):
    if n != None and n.type != 'T':
        global FILE_OUT
        global DOMAIN_LOC
        global LOC
        global GLOBAL_LOC
        # print(n.name, condition, loc_break, loc_continue)
        if n.name == "MulDef":
            LDR(n.children[0], ignore, cur_domain, True)
            LDR(n.children[1], ignore, cur_domain)
            return
        elif n.name == 'FuncDef':
            FILE_OUT.write('define dso_local ')
        elif n.name == "Block":
            domain_num = DOMAIN_LOC
            DOMAIN_LOC += 1
            domain = Domain(domain_num, father = cur_domain)
            if cur_domain:
                cur_domain.children.append(domain)
            if not cur_domain.father:
                print_node(n.children[0], ignore)
            LDR(n.children[1], ignore = ignore, cur_domain = domain, glob = False, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
            if not cur_domain.father:
                print_node(n.children[2], ignore)
            return
        elif n.name == 'VarDecl':
            LDR(n.children[1], ignore, cur_domain, glob)
            return 
        elif n.name == 'ConstDecl':
            LDR(n.children[2], ignore, cur_domain, glob)
            return 
        elif n.name == 'VarDef':
            var = n.children[0]
            # print(var.val)
            assert var.name == 'Ident'
            item = find_var_in_domain(cur_domain, var.val)
            if item:
                print("duplicate var define of %s\n" % (var.val))
                sys.exit(0)
            if glob:
                res = 0
                if len(n.children) == 3:
                    check_val(n.children[2], cur_domain)
                    res = operate_exp(n.children[2], cur_domain, glob)[0]
                    FILE_OUT.write('@g%d = dso_local global i32 %d\n' %(GLOBAL_LOC, res))
                else:
                    FILE_OUT.write('@g%d = dso_local global i32 %d\n' %(GLOBAL_LOC, res))
                cur_domain.item_tab.append(SymbolItem("Var", "int", var.val, cur_domain, '@g' + str(GLOBAL_LOC), res))
                GLOBAL_LOC += 1
                return
            item = SymbolItem(_type = "Var", dataType = "int", name = var.val, domain = cur_domain, loc = '%x' + str(LOC))
            LOC += 1
            cur_domain.item_tab.append(item)
            if len(n.children) == 3:
                FILE_OUT.write('%s = alloca i32\n' % (item.loc))
                res = operate_exp(n.children[2], cur_domain)[0]
                FILE_OUT.write('store i32 %s, i32* %s\n' %(str(res), item.loc))
            else:
                FILE_OUT.write('%s = alloca i32\n' % (item.loc))
            return
        elif n.name == 'ConstDef':
            var = n.children[0]
            item = find_var_in_domain(cur_domain, var.val)
            if item:
                print("duplicate const define of %s\n" % (var.val))
                sys.exit(1)
            if glob:
                res = 0
                if len(n.children) == 3:
                    check_val(n.children[2], cur_domain)
                    res = operate_exp(n.children[2], cur_domain, glob)[0]
                    FILE_OUT.write('@g%d = dso_local global i32 %d\n' %(GLOBAL_LOC, res))
                else:
                    FILE_OUT.write('@g%d = dso_local global i32 %d\n' %(GLOBAL_LOC, res))
                cur_domain.item_tab.append(SymbolItem("Const", "int", var.val, cur_domain, '@g' + str(GLOBAL_LOC), res))
                GLOBAL_LOC += 1
                return
            item = SymbolItem(_type = "Const", dataType = "int", name = var.val, domain = cur_domain, loc = '%x' + str(LOC))
            cur_domain.item_tab.append(item)
            LOC += 1
            FILE_OUT.write('%s = alloca i32\n' % (item.loc))
            check_val(n.children[2], cur_domain)
            res = operate_exp(n.children[2], cur_domain)[0]
            FILE_OUT.write('store i32 %s, i32* %s\n' %(str(res), item.loc))
            return 
        elif n.name == 'VarAssign':
            var = n.children[0]
            print(var.val)
            assert var.name == 'Ident'
            item = find_var_cross_domain(cur_domain, var.val)
            if item:
                if item._type == 'Const':
                    sys.exit(1)
                else:
                    res = operate_exp(n.children[2], cur_domain)[0]
                    FILE_OUT.write('store i32 %s, i32* %s\n' %(str(res), item.loc))
                    return
            sys.exit(1)
        elif n.name == 'return':
            op = operate_exp(n.children[1], cur_domain)
            FILE_OUT.write('ret i32 ' + str(op[0]) + '\n')
            return 
        elif n.name == 'IfElse':
            if_else_operator(n, cur_domain, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
            return 
        elif n.name == 'While':
            while_operate(n, cur_domain)
            return
        elif n.name == 'Break':
            assert loc_break is not None
            FILE_OUT.write('br label %%x%d\n' % (loc_break))
            return 
        elif n.name == 'Cont':
            assert loc_continue is not None
            assert loc_break is not None
            assert condition is not None
            res = operate_exp(condition, cur_domain)
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0]))
            LOC += 1
            FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc_continue, loc_break))
            return 
        elif n.name[-3:] == 'Exp':
            operate_exp(n, cur_domain)
            return

        for idx, child in enumerate(n.children):
            if isinstance(child, AstNode):
                if child.type == 'T':
                    if child.val == 'int' or n.val == 'const':
                        continue
                    else:
                        print_node(child.val, ignore)
                else:
                    LDR(child, ignore, cur_domain, glob, condition, loc_break, loc_continue)
            else:
                print_node(child, ignore)
                
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
    LDR(result, ignore = False, cur_domain = Domain(0), glob = True)

    FILE_IN.close()
    FILE_OUT.close()

if __name__ == '__main__':
    main(sys.argv)
