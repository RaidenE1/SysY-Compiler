# Lab4 `if`语句与条件表达式

> 编译原理第四次实验

## 实验内容

- 本次实验结束后，编译器需要支持 `if`、`else` 条件分支语句以及条件表达式。

## 实现思路

### 1. 条件表达式

1. 在`paser_modules.py`中增添了如下关于条件表达式的文法：

```python
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
```

2. 以及`main.py`中对于`*Exp`节点的处理函数：

```python
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
    elif n.name == 'LAndExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])[0]
            op2 = operate_exp(n.children[2])[0]
            FILE_OUT.write('%%x%d = and i32 %s, %s\n' % (LOC, op1, op2))
            LOC += 1
            return '%x' + str(LOC - 1), False
    elif n.name == 'LOrExp':
        if len(n.children) == 3:
            op1 = operate_exp(n.children[0])[0]
            op2 = operate_exp(n.children[2])[0]
            FILE_OUT.write('%%x%d = or i32 %s, %s\n' % (LOC, op1, op2))
            LOC += 1
            return '%x' + str(LOC - 1), False
```

对于每次涉及到`icmp`的操作，因为结果为`i1`类型，后续处理不方便，所以再次使用一个`zext`函数转为i32类型。即在所有`*Exp`节点的处理和运算中，返回的寄存器均为装在i32类型的寄存器，或者一个i32类型的整数。

### 2. `if-else`语句

1. 在`paser_modules.py`中增添了如下关于条件表达式的文法：

```python
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
```

为`if-else`节点设置单独的`name`，并且通过`children`列表来判断是否有`else`表达式。

2. 以及`main.py`中对于`IfElse`节点的处理函数：

```python
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
```

- 首先依据`children`列表的长度判断是不是需要`else`，然后处理`cond`，在准备br跳转前先将`LOC`变量增加多个，为`if`和`else`的代码块留出位置，然后将`stmt`块节点用`block_operate()`函数处理。
- 在`block_operate()`函数中，输入的节点均为`stmt`，而对与`stmt`节点，还需要判断时普通的代码还是嵌套的`if-else`，如果是嵌套的`if-else`则须递归调用`if-else-operator()`。
- 若为普通代码，则调用`LDR()`中序遍历子树输出。
- 最后在结尾加上强制跳转到`loc_after`代码块的命令，`loc_after`是在之前预留的一个位置，表示整个`if-else`结束后的代码例如return等的代码块。


## 问题

1. 在条件表达式中解释过，整个计算表达式的过程使用的值均为`i32`类型，而在br中需要一个`i1`类型的bool值，所以在每次br命令执行之前，需要把cond的返回值进行一个类型强制转换。zext只能进行i1到i32而不能反过来，所以使用一个`icmp ne`命令，将输入值与0进行比较，得到结果会返回一个`i1`类型的值，并且在不为0时返回`true`，0时返回`false`。

```python
FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0])
```

2. if-else的代码块结束后，函数不会自动跳转到接下来的语句，所以需要给后面的代码单独设置代码块和编号
