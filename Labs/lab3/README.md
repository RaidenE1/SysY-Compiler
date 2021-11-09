# Lab3 局部变量和调用函数

> 编译原理第三次实验

## 实验内容

- 本次实验包括两个部分，编译器需要在 lab 2 的基础上支持以下两个功能：
    - 实现局部变量、局部常量的声明和使用
    - 实现对 miniSysY 库函数的调用(`int getint()`,  `int getch()`,  `void putint(int)`, `void putch(int)`)
    

## 实现思路

简单的列表无法实现复杂的功能，需要更加深层次的数据结构，所以添加了一个`class AstNode`，用来存放语法树的每一个节点，~~再次超大范围重构了~~,通过中序遍历节点来实现遍历语法树。

AstNode结构如下：

```python
class AstNode:
    def __init__(self, type = 'T', children = None, name = None, val = None, const = True, loc = 0):
        self.type = type # 是否为终结符
        self.name = name # 类别
        self.val = val # 名称
        self.const = const # 是否为常量
        self.loc = loc # 内存地址
```

暂时还十分简洁没设计什么重要的功能和属性，这可能也是后面我写了巨大的嵌套`if-else`的原因

对于`*Exp`的节点，但拉出来做特殊处理。显然无法使用字符串+`eval()`的形式，特别定义了函数`operate_exp()`,函数内容如下：

```python
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
                FILE_OUT.write('%%%d = load i32, i32* %%%d\n' % (LOC - 1, VALUE_MAP[res.val].loc))
                # print('pri load')
                return '%' + str(LOC - 1), False
            else:
                print("not int not str")
        else: 
            return operate_exp(n.children[1])
    elif n.name == 'UnaryExp':
        '''
        太长不写
        '''
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
                FILE_OUT.write("%%%d = call i32 @getint()\n" % (LOC))
                LOC += 1
                return '%' + str(LOC - 1), False
            elif n.children[0] == 'getch':
                FILE_OUT.write("%%%d = call i32 @getch()\n" %(LOC))
                LOC += 1
                return '%' + str(LOC - 1), False
            else:
                print('SysFuncOP Error 3')
                exit(0)
        else:
            print('SysFunc Error')
            exit(0)
    elif n.name == 'MulExp':
        '''
        太长不写
        '''
    elif n.name == 'AddExp':
        '''
        太长不写
        '''
    else:
        print('EXP OPERATION ERROR')
        exit(1)
```

省略掉的都是大体差不多的，函数本身是一个递归调用，如果函数的字节点存在`*Exp`节点，则调用这个函数输出。其中`n.name == 'SysFunc'`表示是基本库函数

函数的最终返回结果为一个元组，第一位是一个int表示直接结果或者是一个str表示内存地址，第二位则是一个布尔值表示是否为一个指针(即是否需要load)


## 问题

1. 定义`const`常量时需要考虑`*Exp`不含var，我选择在`ConstDef`语意中递归遍历第二个叶节点中的子节点，确保没有`node.const == True`的情况出现，否则调用`sys.exit(1)`。函数内容如下：

```python
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
```



2. 第二个问题是暂时没考虑库函数内含有多个param的情况，也没考虑`int getarray(int [])`和`void putarray(int, int [])`的情况，有精力再说吧
