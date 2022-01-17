# Lab8 函数

> 编译原理第八次实验

## 实验内容

- 本次实验结束后，编译器在 lab 7 的基础上支持自定义函数以及库函数`getarray`&`putarray`

## 实现思路

### 1. 函数声明

在main函数中添加对FuncDef节点的处理。
- 当子节点个数为5时说明函数为无参函数，写入常规字符串后直接对BLock进行处理。
- 当子节点个数为6时需要取出参数，这里又使用了一个递归，结构与get_brackets和get_init_val类似。
```python
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
```
- 然后遍历取得的参数列表，对于每一个参数需要在该函数所定义的作用域内存放，而作用域是在后面的Block节点中定义的，所以需要给LDR加入参数，将所有的参数传入Block节点的处理函数中。
- 在Block节点如果接收到了item列表，那么说明这个Block是函数的Block，否则可能是if或者else的Block
    - 对于隶属于函数的块，需要声明每一个变量。例如int，传入类型为i32， 但局部变量需要声明一个i32 *作为局部变量的地址。而数组类型因为传入的是地址所以不需要处理。
```python
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

def LDR(n, ignore = False, cur_domain = None, glob = False, condition = None, loc_break = None, loc_continue = None, items = None, func_block = False, func_type = None):
    if n.name == "Block":
        # ......
        if items:
            for it in items:
                it.domain = domain
            itemnew = func_param_decl(items)
            domain.item_tab += itemnew
```
- 在Block节点结束时需要判断是否进行过return，采用全局变量RET来表示。
    - 每当声明函数时初始化为False。
    - 当隶属于函数的Block节点内调用过return时置为True
    - 如果return为False则根据函数类型添加ret。

### 2. FuncExp

在之前定义的文法中，有特定的FuncExp节点，在节点内增加自定义函数的调用即可。
```python
params = get_params(n.children[2])
params_res = [operate_exp(x, cur_domain, glob)[0] for x in params]
if item:
    fType = item._type
    f_param = item.params
    print(item.name, f_param)
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
            assert temp_dim == f_param[idx].dim                         # 维度检查
    FILE_OUT.write(')\n')
    if fType != 'void':
        return '%x' + str(LOC - 1), False
```
同时在输入时进行一个维度检查，输入数组的维度必须与声明函数时定义的维度相同。get_mindim函数取出一个数组中所有参数的维度。其中变量为0，数组变量的维度为`数组的维度 - 中括号的数量`，其他则为空。
```python
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
```
### 总结

这次写的比较随意，写了个框架然后对着测试点一个一个debug...... 根据情况添加ret void。包括lab7改的and指令的bug，把or也改了之后忘加'%'了，导致calculator那个点报了段错误。2k+的IR。。。然后交到lab7里找到了一个WA这才过。有一些问题在这个测试机没有暴露出来，看看挑战实验的结果如何吧。