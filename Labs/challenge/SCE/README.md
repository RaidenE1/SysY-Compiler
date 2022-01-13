# Challenge: Short_circuit evaluation

> 挑战实验: 短路求值

## 实验内容

逻辑与和逻辑或操作符要求总是计算其左操作数，只有在仅靠左操作数的值无法确定该逻辑表达式的结果时，才会求解其右操作数，这被称为短路求值。

在之前的测试样例中，并没有针对逻辑表达式的短路求值特性进行评测，在这个实验中，编译器需要实现逻辑表达式的短路求值功能。

## 实现思路

- 当遇到`A && B 且 A == False`时直接跳过B的运行
- 当遇到`A || B 且 A == True`时直接跳过B的运行

如果再大胆一点。。。

- 文法中规定不会出现类似嵌套的`&&`和`||`。所以所有的条件都是平行的。那么当遇到一个`False`，且紧跟`&&`时，可以连续跳过所有的`&&`，直到出现`||`为止。
- 同理，当遇到一个`True`，且紧跟`||`时，可以连续跳过所有的`||`，直到出现`&&`为止。

具体实现如下：
```python
def if_else_operator(n, cur_domain, condition = None, loc_break = None, loc_continue = None):
    # ......
    cond_list = get_LEXP(n.children[2])
    if len(n.children) == 5:
        # ......
        for i in range(0, len(cond_list), 2): # 表达式和关系符交替出现，所以+=2
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
        # ......
```
其中`cond_list`是对形如 `A && B || C ......`的多条件表达式进行条件和关系的提取结果。处理函数如下：
```python
def get_LEXP(n):
    if n.name == 'LOrExp':
        return get_LEXP(n.children[0]) + ['or'] + get_LEXP(n.children[2])
    elif n.name == 'LAndExp':
        return get_LEXP(n.children[0]) + ['and'] + get_LEXP(n.children[2])
    elif n.name[-3:] == 'Exp':
        return [n]
```
对于上述例子，提取结果为：`[A, 'and', B, 'or', C]`其中每个条件为一个`AstNode`对象。