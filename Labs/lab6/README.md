# Lab6 循环

> 编译原理第六次实验

## 实验内容

- 本次实验结束后，编译器需要在 lab 5 的基础上支持 `while` 循环、`continue` 和 `break` 语句。

## 实现思路

### 1. while循环

其实与`If-Else`类似，新建基本块，但在结尾需要加入判断条件，如果条件仍成立那么需要跳转到基本块头部，构成循环。万幸的是在`block_operate`函数中已经搭建好了类似的逻辑：

```python
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
```

`loc`指当前基本块的序号，`loc_after`指的是当前基本块之后的基本块的序号。`cond`是*while*的条件，如果`cond`不为空的话那么在跳转的时候需要判断`cond`是否为假，否则直接跳转到`loc_after`标记的基本块就好了，而且这个变量只有在`while_operate`函数调用`block_operate`时会被传入。

`while_operate`如下：

```python
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
    LOC_BREAK = loc_after
    LOC_CONTINUE = loc
    block_operate(stmt, loc, loc_after, cur_domain, cond, cond, loc_after, loc)
    FILE_OUT.write('x%d:\n'%(loc_after))
```

### 2. continue & break

没有采用助教建议的回填策略。通过`while_operate`函数和`block_operate`函数的内容可以发现，在生成每一个基本块时(*while/if*)，我都会传递两个变量，一个是当前块的loc(loc)，另一个是提前预留出来的后续块的loc(loc_after)。也就是代码中全局变量`LOC`在产生每一个块的时候要+=2的原因。所以对于`break`语句，只需要跳转到`loc_after`标记的基本块。对于*continue*语句，同时传递*while*的条件，进行一个类似循环体结束时对于循环条件的判断。这也是`block_operate`中`cond`和`condition`分别的用处。

在递归语法树的函数中：(`LDR`的参数也变得越来越过分了。。。)

```python
def LDR(n, ignore = False, cur_domain = None, glob = False, condition = None, loc_break = None, loc_continue = None):
    if n != None and n.type != 'T':
        # ......
        if n.name == 'Break':
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
        # ......
```



## 问题

1. 开始写循环时直接一个跳转进入了循环体，忽略了在第一次进入循环前也需要进行条件判断，如果不满足则直接跳转到`loc_after`.
2. 这种写法应该会导致很多多余的条件判断，~~但可以继续堆叠屎山~~，包括之前的变量处理，对于`icmp`的结果强转`i32`，遇到下一条指令是`br`时还要强转`i1`，会导至这种情况：

```
%x9 = icmp slt i32 %x6, %x8 // 条件表达式的结果，i1类型
%x10 = zext i1 %x9 to i32 // 代码默认转为i32类型
%x11 = icmp ne i32 %x10, 0 // 因为需要跟据条件表达式跳转，所以还需要强转为i1类型
br i1 %x11, label %x4, label %x5
```

