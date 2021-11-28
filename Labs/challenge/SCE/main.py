from re import A
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

RET = False

def lexer_init(text):
    lexer = lex.lex(module = tokrules)
    lexer.input(text)
    return lexer

def get_mul(l):
    res = 1
    for i in l:
        assert isinstance(i, int)
        res *= i
    return res

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
            if n.name == 'Ident' or n.name == 'ArrVal':
                item = find_var_cross_domain(domain, n.val)
                if (not item) or item._type == 'Var':
                    print('var int const')
                    sys.exit(1)
        else:
            for child in n.children:
                check_val(child, domain)

def get_mindim(n, cur_domain):
    if isinstance(n, int) or isinstance(n, str):
        return [0]
    elif n.name == 'Ident':
        item = find_var_cross_domain(cur_domain, n.val)
        if item.dataType == 'Arr':
            return [item.dim]
        return [0]
    elif n.name == 'ArrVal':
        item = find_var_cross_domain(cur_domain, n.val)
        print(n.children[1], len(get_brackets(n.children[1])))
        return [item.dim - len(get_brackets(n.children[1]))]
    else:
        res = []
        for child in n.children:
            res += get_mindim(child, cur_domain)
        return res

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
            item = find_var_cross_domain(cur_domain, var.val)
            if not item:
                print('item not defined')
                sys.exit(1)
            elif item.dataType == 'int':
                if glob:
                    return item.val, False
                LOC += 1
                FILE_OUT.write('%%x%d = load i32, i32* %s\n' % (LOC - 1, item.loc))
                return '%x' + str(LOC - 1), False
            elif item.dataType == 'Arr':
                if len(var.children) == 0:
                    FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
                    LOC += 1
                    FILE_OUT.write(', i32 0')
                    if item.val != 'i32':
                        FILE_OUT.write(', i32 0')
                    FILE_OUT.write('\n')
                    return '%x' + str(LOC - 1), False
                _brackets = get_brackets(var.children[1])
                brackets = []
                for x in _brackets:
                    _res = operate_exp(x, cur_domain, glob)
                    res_loc = _res[0]
                    if _res[1]:
                        FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res_loc))
                        LOC += 1
                        res_loc= '%x' + str(LOC - 1)
                    brackets.append(res_loc)
                item = find_var_cross_domain(cur_domain, var.val)
                if not item:
                    print('item not defined')
                    sys.exit(1)
                LOC += 2
                res_pos_ptr = LOC - 2
                res_pos = LOC - 1
                FILE_OUT.write('%%x%d = alloca i32\nstore i32 0, i32* %%x%d\n%%x%d = load i32, i32* %%x%d\n' %(res_pos_ptr, res_pos_ptr, res_pos, res_pos_ptr))
                changed = False
                if len(brackets) < len(item.dimL):
                    for idxx in range(len(brackets)):
                        val = brackets[idxx]
                        if val != 0:
                            LOC += 2
                            FILE_OUT.write('%%x%d = mul i32 %s, %s \n' % (LOC - 2, val, get_mul(item.dimL[idxx + 1:])))
                            FILE_OUT.write('%%x%d = add i32 %%x%d, %%x%d\n' % (LOC - 1, res_pos, LOC - 2))
                            res_pos = LOC - 1
                            changed = True
                else:
                    for idxx in range(len(brackets) - 1):
                        val = brackets[idxx]
                        if val != 0:
                            LOC += 2
                            FILE_OUT.write('%%x%d = mul i32 %s, %s \n' % (LOC - 2, val, get_mul(item.dimL[idxx + 1:])))
                            FILE_OUT.write('%%x%d = add i32 %%x%d, %%x%d\n' % (LOC - 1, res_pos, LOC - 2))
                            res_pos = LOC - 1
                            changed = True
                    if brackets[-1] != 0:
                        LOC += 1
                        FILE_OUT.write('%%x%d = add i32 %%x%d, %s\n' % (LOC - 1, res_pos, brackets[-1]))
                        res_pos = LOC - 1
                        changed = True
                if changed:
                    FILE_OUT.write("store i32 %%x%d, i32* %%x%d\n" % (res_pos, res_pos_ptr))
                FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
                LOC += 1
                if item.val != 'i32':
                    FILE_OUT.write(', i32 0')
                FILE_OUT.write(', i32 %%x%d\n' % (res_pos))
                # LOC += 1
                # FILE_OUT.write('%%x%d = load i32, i32* %%x%d\n' % (LOC - 1, LOC - 2))
                return '%x' + str(LOC - 1), True

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
        SYS_FUNC = ['getint', 'getch', 'putint', 'putch', 'getarray', 'putarray']
        func_name = n.children[0]
        item = find_var_cross_domain(cur_domain, func_name)
        if func_name not in SYS_FUNC and not item:
            print('func not defined')
            sys.exit(1)
        if len(n.children) == 4:
            params = get_params(n.children[2])
            _params_res = []
            params_res = []
            for _ in params:
                _res = operate_exp(_, cur_domain, glob)
                res_loc = _res[0]
                if _res[1]:
                    FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res_loc))
                    LOC += 1
                    res_loc = '%x' + str(LOC - 1)
                _params_res.append(_res[0])
                params_res.append(res_loc)
            if item:
                fType = item._type
                f_param = item.params
                if fType != 'void':
                    FILE_OUT.write('%%x%d = ' % (LOC))
                    LOC += 1
                if fType == 'int':
                    fType = 'i32'
                FILE_OUT.write("call %s @%s(" %(fType, item.name))
                for idx, p in enumerate(item.typel):
                    if idx > 0:
                        FILE_OUT.write(', ')
                    FILE_OUT.write('%s %s' % (p, params_res[idx]))
                    if get_mindim(params[idx], cur_domain) and f_param[idx].dim:
                        temp_dim = min(get_mindim(params[idx], cur_domain))
                        print(temp_dim, f_param[idx].dim, idx)
                        assert temp_dim == f_param[idx].dim
                FILE_OUT.write(')\n')
                if fType != 'void':
                    return '%x' + str(LOC - 1), False
            elif n.children[0] == 'putint':
                FILE_OUT.write("call void @putint(i32 %s)\n" %(params_res[0]))
            elif n.children[0] == 'putch':
                FILE_OUT.write("call void @putch(i32 %s)\n" %(params_res[0]))
            elif n.children[0] == 'putarray':
                FILE_OUT.write("call void @putarray(i32 %s, i32* %s)\n" %(params_res[0], _params_res[1]))
            elif n.children[0] == 'getarray':
                FILE_OUT.write("%%x%d = call i32 @getarray(i32* %s)\n" %(LOC, _params_res[0]))
                LOC += 1
                return '%x' + str(LOC - 1), False
            else:
                print('SysFuncOP Error')
                sys.exit(0)
        elif len(n.children) == 3:
            if item:
                fType = item._type
                if fType != 'void':
                    FILE_OUT.write('%%x%d = ' % (LOC))
                    LOC += 1
                if fType == 'int':
                    fType = 'i32'
                FILE_OUT.write("call %s @%s()\n" %(fType, item.name))
                if fType != 'void':
                    return '%x' + str(LOC - 1), False
            else:
                if n.children[0] == 'getint':
                    FILE_OUT.write("%%x%d = call i32 @getint()\n" % (LOC))
                    LOC += 1
                elif n.children[0] == 'getch':
                    FILE_OUT.write("%%x%d = call i32 @getch()\n" %(LOC))
                    LOC += 1
                return '%x' + str(LOC - 1), False
        else:
            sys.exit(0)
    elif n.name == 'MulExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0], cur_domain, glob)
            loc1 = op1[0]
            if op1[1]:
                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, loc1))
                LOC += 1
                loc1 = '%x' + str(LOC - 1)
            op2 = operate_exp(n.children[2], cur_domain, glob)
            loc2 = op2[0]
            if op2[1]:
                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, loc2))
                LOC += 1
                loc2 = '%x' + str(LOC - 1)
            if n.children[1] == '//':
                if isinstance(loc1, str) or isinstance(loc2, str):
                    FILE_OUT.write("%%x%d = sdiv i32 %s, %s\n" %(LOC, str(loc1), str(loc2)))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(loc1) + ' // ' + str(loc2))), False
            elif n.children[1] == '*':
                if isinstance(loc1, str) or isinstance(loc2, str):
                    FILE_OUT.write("%%x%d = mul i32 %s, %s\n" %(LOC, str(loc1), str(loc2)))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(loc1) + ' * ' + str(loc2))), False
            elif n.children[1] == '%':
                if isinstance(loc1, str) or isinstance(loc2, str):
                    FILE_OUT.write("%%x%d = srem i32 %s, %s\n" %(LOC, str(loc1), str(loc2)))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    if op1 >= 0 :
                        sign = 1
                    else:
                        sign = -1
                    return sign * int(eval(str(abs(loc1)) + ' % ' + str(abs(loc2)))), False
            else:
                print('MulExp OP Error')
                exit(1)
    elif n.name == 'AddExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0], cur_domain, glob)
            loc1 = op1[0]
            if op1[1]:
                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, loc1))
                LOC += 1
                loc1 = '%x' + str(LOC - 1)
            op2 = operate_exp(n.children[2], cur_domain, glob)
            loc2 = op2[0]
            if op2[1]:
                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, loc2))
                LOC += 1
                loc2 = '%x' + str(LOC - 1)
            if n.children[1] == '+':
                if isinstance(loc1, str) or isinstance(loc1, str):
                    FILE_OUT.write("%%x%d = add i32 %s, %s\n" %(LOC, str(loc1), str(loc2)))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(loc1) + ' + ' + str(loc2))), False
            elif n.children[1] == '-':
                if isinstance(loc1, str) or isinstance(loc2, str):
                    FILE_OUT.write("%%x%d = sub i32 %s, %s\n" %(LOC, str(loc1), str(loc2)))
                    LOC += 1
                    return '%x' + str(LOC - 1), False
                else:
                    return int(eval(str(loc1) + ' - ' + str(loc2))), False
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
            op1 = operate_exp(n.children[0], cur_domain, glob)
            loc1 = op1[0]
            if op1[1]:
                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, loc1))
                LOC += 1
                loc1 = '%x' + str(LOC - 1)
            op2 = operate_exp(n.children[2], cur_domain, glob)
            loc2 = op2[0]
            if op2[1]:
                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, loc2))
                LOC += 1
                loc2 = '%x' + str(LOC - 1)
            op = OpMap.get(n.children[1], None)
            assert op is not None
            FILE_OUT.write('%%x%d = icmp %s i32 %s, %s\n' % (LOC, op, loc1, loc2))
            LOC += 1
            FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('EqExp len Error')
            exit(1)
    elif n.name == 'LAndExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0], cur_domain, glob)[0]
            op2 = operate_exp(n.children[2], cur_domain, glob)[0]
            LOC += 3
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC - 3, op1))
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC - 2, op2))
            FILE_OUT.write('%%x%d = and i1 %%x%d, %%x%d\n' % (LOC - 1, LOC - 3, LOC - 2))
            FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('LAndExp len Error')
            exit(1)
    elif n.name == 'LOrExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0], cur_domain)[0]
            op2 = operate_exp(n.children[2], cur_domain)[0]
            LOC += 3
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC - 3, op1))
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC - 2, op2))
            FILE_OUT.write('%%x%d = or i1 %%x%d, %%x%d\n' % (LOC - 1, LOC - 3, LOC - 2))
            FILE_OUT.write('%%x%d = zext i1 %%x%d to i32\n' %(LOC, LOC - 1))
            LOC += 1
            return '%x' + str(LOC - 1), False
        else:
            print('LAndExp len Error')
            exit(1)
    else:
        print('EXP OPERATION ERROR')
        exit(1)

def get_LEXP(n):
    if n.name == 'LOrExp':
        return get_LEXP(n.children[0]) + ['or'] + get_LEXP(n.children[2])
    elif n.name == 'LAndExp':
        return get_LEXP(n.children[0]) + ['and'] + get_LEXP(n.children[2])
    elif n.name[-3:] == 'Exp':
        return [n]

def if_else_operator(n, cur_domain, condition = None, loc_break = None, loc_continue = None):
    global FILE_OUT
    global LOC
    loc_after = 0
    assert n.name == 'IfElse'
    cond_list = get_LEXP(n.children[2])
    if len(n.children) == 5:
        cur_loc = LOC
        LOC += ((len(cond_list)+1)//2 + 2)
        loc_after = LOC - 1
        loc = LOC - 2
        for i in range(0, len(cond_list), 2):
            cond = cond_list[i]
            cond_res = operate_exp(cond, cur_domain)[0]
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, cond_res))
            LOC += 1
            if i == len(cond_list) - 1:
                if cond_list[i-1] == 'and':
                    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc, loc_after))
                else:
                    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc, loc_after))
                continue
            if cond_list[i+1] == 'and':
                FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, cur_loc + 1, loc_after))
            else:
                FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc, cur_loc + 1))
            if i != len(cond_list) - 1:
                FILE_OUT.write('x%d:\n' % (cur_loc + 1))
            cur_loc += 1
        stmt = n.children[4]
        block_operate(stmt, loc, loc_after, cur_domain, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
    elif len(n.children) == 7:
        cur_loc = LOC
        LOC += ((len(cond_list)+1)//2 + 3)
        loc_after = LOC - 1
        loc2 = LOC - 2
        loc1 = LOC - 3
        for i in range(0, len(cond_list), 2):
            cond = cond_list[i]
            cond_res = operate_exp(cond, cur_domain)[0]
            FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, cond_res))
            LOC += 1
            if i == len(cond_list) - 1:
                if cond_list[i-1] == 'and':
                    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc1, loc2))
                else:
                    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc1, loc2))
                continue
            if cond_list[i+1] == 'and':
                j = i + 1
                while j < len(cond_list) and cond_list[j] == 'and':
                    j += 2
                print(j,i)
                if j > len(cond_list) :
                    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, cur_loc + 1, loc2))
                else:
                    FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, cur_loc + 1, cur_loc + 1 + (j-i-1)//2))
            else:
                FILE_OUT.write('br i1 %%x%d, label %%x%d, label %%x%d\n' %(LOC - 1, loc1, cur_loc + 1))
            FILE_OUT.write('x%d:\n' % (cur_loc + 1))
            cur_loc += 1
        stmt1 = n.children[4]
        stmt2 = n.children[6]
        block_operate(stmt1, loc1, loc_after, cur_domain, condition = condition, loc_break = loc_break, loc_continue = loc_continue)
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

def get_brackets(n):
    if len(n.children) == 3:
        return [n.children[1]]
    else:
        return [n.children[1]] + get_brackets(n.children[3])

def get_arr_name(brackets, pos):
    if pos == len(brackets):
        return ['i32']
    else:
        head = ['['+str(brackets[pos]), 'x'] 
        bottle = get_arr_name(brackets, pos+1)
        bottle[-1] += ']'
        return head + bottle

def get_add_init_val(n, p, pos, cur_domain, glob):
    res = get_init_val(n.children[1], 0, pos+[p], cur_domain, glob)
    if len(n.children) == 3:
        res += get_add_init_val(n.children[2], p + 1, pos, cur_domain, glob)
    return res

def get_init_val(n, p, pos, cur_domain, glob = False):
    global LOC
    if n.name[-3:] == "Exp" or len(n.children) == 1:
        val = operate_exp(n, cur_domain, glob)
        res_loc = val[0]
        if val[1]:
            FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res_loc))
            LOC += 1
            res_loc= '%x' + str(LOC - 1)
        arr_node = Array(pos, res_loc)
        return [arr_node]
    elif len(n.children) == 3:
        return get_init_val(n.children[1], 0, pos + [p], cur_domain, glob)
    elif len(n.children) == 4:
        return get_init_val(n.children[1], 0, pos + [p], cur_domain, glob) + get_add_init_val(n.children[2], 1, pos, cur_domain, glob)
    else:
        return []

def get_pos(val_pos, arr_len):
    res = 0
    for i in range(len(val_pos) - 1):
        res += val_pos[i] * get_mul(arr_len[i + 1:])
    res += val_pos[-1]
    return res

def get_add_params(n):
    if len(n.children) == 2:
        return [n.children[1]]
    else:
        return [n.children[1]] + get_add_params(n.children[2])

def get_params(n):
    if len(n.children) == 1:
        return [n.children[0]]
    else:
        return [n.children[0]] + get_add_params(n.children[1])

def arr_decl(n, cur_domain, glob = False):
    global LOC
    global FILE_OUT
    global GLOBAL_LOC
    _name = n.children[0]
    # print(_name)
    check_val(n.children[1], cur_domain)
    _brackets = get_brackets(n.children[1])
    brackets = [operate_exp(x, cur_domain, glob = True)[0] for x in _brackets]
    for res in brackets:
        if not isinstance(res, int):
            print('not init val in arr len')
            sys.exit(0)
    arr_name = '[' + str(get_mul(brackets)) + ' x ' + 'i32]'
    dim = len(brackets)
    item = find_var_in_domain(cur_domain, _name)
    if item:
        sys.exit(0)
    if n.name == 'ConstArr':
        val_list = get_init_val(n.children[3], 0, [], cur_domain, glob)
        check_val(n.children[3], cur_domain)
        if glob:
            item_glob = SymbolItem('Const', 'Arr', _name, cur_domain, '@g'+str(GLOBAL_LOC), arr_name, dim, brackets)
            GLOBAL_LOC += 1
            FILE_OUT.write('%s = dso_local constant %s ' % (item_glob.loc, item_glob.val))
            val_list = get_init_val(n.children[3], 0, [], cur_domain, glob)
            cur_domain.item_tab.append(item_glob)
            if val_list == None:
                FILE_OUT.write('zeroinitializer\n')
            else:
                val_ptr = 0
                arr_ptr = 0
                FILE_OUT.write('[')
                arr_len = get_mul(item_glob.dimL)
                while arr_ptr < arr_len or val_ptr < len(val_list):
                    val_pos = 0
                    if val_ptr < len(val_list):
                        val_pos = get_pos(val_list[val_ptr].pos, item_glob.dimL)
                    if arr_ptr == val_pos:
                        FILE_OUT.write('i32 %s' % (val_list[val_ptr].val))
                        val_ptr += 1
                    else:
                        FILE_OUT.write('i32 0')
                    arr_ptr += 1
                    if arr_ptr < arr_len:
                        FILE_OUT.write(', ')
                FILE_OUT.write(']\n')  
            return 
        item = SymbolItem('Const', 'Arr', _name, cur_domain, '%x'+str(LOC), arr_name, dim, brackets)
        cur_domain.item_tab.append(item)
        LOC += 1
        FILE_OUT.write('%s = alloca %s\n' % (item.loc, item.val))
        FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
        LOC += 1
        FILE_OUT.write(', i32 0, i32 0\n')
        FILE_OUT.write('call void @memset(i32* %%x%d,i32 %d,i32 %d)\n' % (LOC - 1, 0, 4*get_mul(brackets)))
        for idx, arr_node in enumerate(val_list):
            if arr_node == None:
                continue
            elif len(arr_node.pos) != len(brackets):
                print('pos not match')
                sys.exit(1)
            FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
            LOC += 1
            FILE_OUT.write(', i32 0')
            res_pos = 0
            for idxx in range(len(arr_node.pos) - 1):
                ele_pos = arr_node.pos[idxx]
                if ele_pos >= brackets[idxx]:
                    print('pos out of bound')
                    sys.exit(1)
                else:
                    res_pos += ele_pos * get_mul(brackets[idxx + 1:])  
            res_pos += arr_node.pos[-1]  
            FILE_OUT.write(', i32 %d\n' % (res_pos))
            FILE_OUT.write('store i32 %s, i32* %%x%d\n' %(arr_node.val, LOC - 1))
    else:
        if glob:
            if len(n.children) == 2:
                item_glob = SymbolItem('Var', 'Arr', _name, cur_domain, '@g'+str(GLOBAL_LOC), arr_name, dim, brackets)
                FILE_OUT.write('%s = dso_local global %s zeroinitializer\n' % (item_glob.loc, item_glob.val))
                cur_domain.item_tab.append(item_glob)
                GLOBAL_LOC += 1
            else:
                item_glob = SymbolItem('Var', 'Arr', _name, cur_domain, '@g'+str(GLOBAL_LOC), arr_name, dim, brackets)
                GLOBAL_LOC += 1
                FILE_OUT.write('%s = dso_local global %s ' % (item_glob.loc, item_glob.val))
                val_list = get_init_val(n.children[3], 0, [], cur_domain, glob)
                cur_domain.item_tab.append(item_glob)
                if val_list == None:
                    FILE_OUT.write('zeroinitializer\n')
                else:
                    val_ptr = 0
                    arr_ptr = 0
                    FILE_OUT.write('[')
                    arr_len = get_mul(item_glob.dimL)
                    while arr_ptr < arr_len:
                        val_pos = 0
                        if val_ptr < len(val_list):
                            val_pos = get_pos(val_list[val_ptr].pos, item_glob.dimL)
                        if arr_ptr == val_pos:
                            FILE_OUT.write('i32 %s' % (val_list[val_ptr].val))
                            val_ptr += 1
                        else:
                            FILE_OUT.write('i32 0')
                        arr_ptr += 1
                        if arr_ptr < arr_len:
                            FILE_OUT.write(', ')
                    FILE_OUT.write(']\n')  
            return 
        item = SymbolItem('Var', 'Arr', _name, cur_domain, '%x'+str(LOC), arr_name, dim, brackets)
        cur_domain.item_tab.append(item)
        LOC += 1
        FILE_OUT.write('%s = alloca %s\n' % (item.loc, item.val))
        FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
        LOC += 1
        FILE_OUT.write(', i32 0, i32 0\n')
        FILE_OUT.write('call void @memset(i32* %%x%d,i32 %d,i32 %d)\n' % (LOC - 1, 0, 4*get_mul(brackets)))
        if len(n.children) == 4:
            val_list = get_init_val(n.children[3], 0, [], cur_domain, glob)
            if val_list == None:
                return
            for idx, arr_node in enumerate(val_list):
                if arr_node == None:
                    continue
                if len(arr_node.pos) != len(brackets):
                    print('pos not match')
                    sys.exit(1)
                FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
                LOC += 1
                FILE_OUT.write(', i32 0')
                res_pos = 0
                for idxx in range(len((arr_node.pos)) - 1):
                    ele_pos = arr_node.pos[idxx]
                    if ele_pos >= brackets[idxx]:
                        print('pos out of bound')
                        sys.exit(1)
                    else:
                        res_pos += ele_pos * get_mul(brackets[idxx + 1:])
                res_pos += arr_node.pos[-1]  
                FILE_OUT.write(', i32 %d\n' % (res_pos))
                FILE_OUT.write('store i32 %s, i32* %%x%d\n' %(arr_node.val, LOC - 1))

def func_param_decl(items):
    global LOC 
    res = []
    for idx, item in enumerate(items):
        if item.dataType == 'int':
            FILE_OUT.write('%%x%d = alloca i32\n' % (LOC))
            LOC += 1
            FILE_OUT.write('store i32 %s, i32* %%x%d\n' % (item.loc, LOC - 1))
            item.loc = '%x' + str(LOC - 1)
        res.append(item)
    return res

def count_brackets(n):
    if len(n.children) == 4:
        return [AstNode('NT', [AstNode('T', None, 'Number', 1)], 'PriExp')]
    else:
        return [AstNode('NT', [AstNode('T', None, 'Number', 1)], 'PriExp')] + get_brackets(n.children[4])
                    
def LDR(n, ignore = False, cur_domain = None, glob = False, condition = None, loc_break = None, loc_continue = None, items = None, func_block = False, func_type = None):
    if n != None and n.type != 'T':
        global FILE_OUT
        global DOMAIN_LOC
        global LOC
        global GLOBAL_LOC
        global RET
        # print(n.name, condition, loc_break, loc_continue)
        if n.name == "MulDef":
            LDR(n.children[0], ignore, cur_domain, True)
            LDR(n.children[1], ignore, cur_domain)
            return
        elif n.name == 'FuncDef':
            FILE_OUT.write('define dso_local ')
            func_name = n.children[1]
            item = SymbolItem(n.children[0], 'Func', func_name, cur_domain, 0)
            cur_domain.item_tab.append(item)
            if n.children[0] == 'int':
                FILE_OUT.write('i32 ')
            elif n.children[0] == 'void':
                FILE_OUT.write('void ')
            else:
                print('no type found')
                sys.exit(1)
            FILE_OUT.write('@' + n.children[1] + '(')
            if len(n.children) == 5:
                FILE_OUT.write(')\n')
                ft = n.children[0]
                if ft == 'int':
                    ft = 'i32'
                LDR(n.children[4], ignore, cur_domain, func_block = True, func_type = ft)
            else:
                params = get_params(n.children[3])
                pType = []
                items = []
                for idx, p in enumerate(params):
                    if idx > 0:
                        FILE_OUT.write(', ')
                    if len(p.children) == 2:
                        FILE_OUT.write('i32 %%x%d' % (LOC))
                        LOC += 1
                        pType.append('i32')
                        items.append(SymbolItem('Var', 'int', p.children[1], None, '%x' + str(LOC - 1)))
                    else:
                        FILE_OUT.write('i32* %%x%d' % (LOC))
                        LOC += 1
                        pType.append('i32*')
                        _brackets = count_brackets(p)
                        brackets = [operate_exp(x, cur_domain)[0] for x in _brackets]
                        items.append(SymbolItem('Var', 'Arr', p.children[1], None, '%x' + str(LOC - 1), 'i32', dims = len(brackets), dimL = brackets))
                item.typel = pType
                FILE_OUT.write(')\n')
                ft = n.children[0]
                if ft == 'int':
                    ft = 'i32'
                item.params = items
                LDR(n.children[5], ignore, cur_domain, items = items, func_block = True, func_type = ft)
            return
        elif n.name == "Block":
            domain_num = DOMAIN_LOC
            DOMAIN_LOC += 1
            domain = Domain(domain_num, father = cur_domain)
            if func_block:
                RET = False
            if cur_domain:
                cur_domain.children.append(domain)
            if not cur_domain.father:
                print_node(n.children[0], ignore)
            if items:
                for it in items:
                    it.domain = domain
                itemnew = func_param_decl(items)
                domain.item_tab += itemnew
            LDR(n.children[1], ignore = ignore, cur_domain = domain, glob = False, condition = condition, loc_break = loc_break, loc_continue = loc_continue, func_type = func_type)
            if func_block :
                FILE_OUT.write('ret %s ' % (func_type))
                if func_type == 'i32':
                    FILE_OUT.write('0')
                FILE_OUT.write('\n')
            if not cur_domain.father:
                print_node(n.children[2], ignore)
            return
        elif n.name == 'VarDecl':
            LDR(n.children[1], ignore, cur_domain, glob)
            return 
        elif n.name == 'ConstDecl':
            LDR(n.children[2], ignore, cur_domain, glob)
            return 
        elif n.name == 'VarArr' or n.name == 'ConstArr':
            arr_decl(n, cur_domain, glob)
            return
        elif n.name == 'VarDef':
            var = n.children[0]
            # print(var.val, n.children)
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
            item.val = res
            FILE_OUT.write('store i32 %s, i32* %s\n' %(str(res), item.loc))
            return 
        elif n.name == 'VarAssign':
            var = n.children[0]
            item = find_var_cross_domain(cur_domain, var.val)
            if item:
                if item._type == 'Const':
                    print('const assign')
                    sys.exit(1)
                else:
                    if item.dataType == 'Arr':
                        _brackets = get_brackets(var.children[1])
                        assert item.dim == len(_brackets)
                        res = operate_exp(n.children[2], cur_domain, glob)
                        brackets = []
                        for x in _brackets:
                            _res = operate_exp(x, cur_domain, glob)
                            res_loc = _res[0]
                            if _res[1]:
                                FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res_loc))
                                LOC += 1
                                res_loc= '%x' + str(LOC - 1)
                            brackets.append(res_loc)
                        LOC += 2
                        res_pos = 0
                        for idxx in range(len(brackets) - 1):
                            val = brackets[idxx]
                            if val != 0:
                                LOC += 2
                                FILE_OUT.write('%%x%d = mul i32 %s, %s\n' % (LOC - 2, val, get_mul(item.dimL[idxx + 1:])))
                                FILE_OUT.write('%%x%d = add i32 %s, %%x%d\n' % (LOC - 1, res_pos, LOC - 2))
                                res_pos = '%x' + str(LOC - 1)
                        if brackets[-1] != 0:
                            LOC += 1
                            FILE_OUT.write('%%x%d = add i32 %s, %s\n' % (LOC - 1, res_pos, brackets[-1]))
                            res_pos = '%x' + str(LOC - 1)
                        FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
                        LOC += 1
                        if item.val != 'i32':
                            FILE_OUT.write(', i32 0')
                        FILE_OUT.write(', i32 %s\n' % (res_pos))
                        FILE_OUT.write('store i32 %s, i32* %%x%d\n' % (res[0], LOC - 1))
                    else:
                        res = operate_exp(n.children[2], cur_domain)[0]
                        FILE_OUT.write('store i32 %s, i32* %s\n' %(str(res), item.loc))
                    return
            print('item not find')
            sys.exit(1)
        elif n.name == 'return':
            if len(n.children) == 2:
                FILE_OUT.write('ret void\n')
            else:
                op = operate_exp(n.children[1], cur_domain)
                res_loc = op[0]
                if op[1]:
                    FILE_OUT.write("%%x%d = load i32, i32* %s\n" % (LOC, res_loc))
                    LOC += 1
                    res_loc= '%x' + str(LOC - 1)
                FILE_OUT.write('ret i32 ' + str(res_loc) + '\n')
            if func_type:
                RET = True
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
    FILE_OUT.write("declare i32 @getch()\ndeclare void @putch(i32)\ndeclare i32 @getint()\ndeclare void @putint(i32)\ndeclare void @memset(i32*, i32, i32)\ndeclare i32 @getarray(i32*)\ndeclare void @putarray(i32, i32*)\n")
    lexer = lexer_init(text)
    print(text)
    # tok = lexer.token()
    # while tok:
    #     print(tok)
    #     tok = lexer.token()
    result = run_parser(text, lexer)
    LDR(result, ignore = False, cur_domain = Domain(0), glob = True)

    FILE_IN.close()
    FILE_OUT.close()

if __name__ == '__main__':
    main(sys.argv)
