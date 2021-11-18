# Lab5 作用域与全局变量

> 编译原理第五次实验
>
> 18351015 张津赫

## 实验内容

- 本次实验结束后，编译器需要在 lab 4 的基础上支持变量作用域的一些区分及全局变量.

## 实现思路

### 1. 作用域

在`ast_modules.py`中添加了两个类: `SymbolItem`和`Domain`

```python
class SymbolItem: # 符号表
    def __init__(self, _type, dataType, name, domain, loc, val = None):
        self._type = _type # ID类型，变量，数组，函数
        self.dataType = dataType
        self.name = name # ID名字
        self.domain = domain
        self.loc = loc
        self.val = val

class Domain: # 作用域
    def __init__(self, num, children = None, father = None):
        self.num = num
        if not children:
            self.children = []
        else:
            self.children = children
        self.father = father
        self.item_tab = []
```

- `SymbolItem`和`AstNode`区别不大

- `Domain`类标记一个作用域，其中`num`为作用域标号，~~可能没什么用？~~，`children`是这个作用域内的定义的所有子作用域的列表，`father`表示包含这个作用域的父作用域，即`father`作用域内定义了`self`。现在整个代码的所有作用域被构建成了一棵树。最外层是全局变量的作用域。在查询变量是否被定义时，从`cur_domain`的`item_tab`查起，递归查找`cur_domain.father`，直到找到定义变量的作用域或者`cur_domain == None`为止。
- item_tab代表变量表，储存在作用域内有效的局部变量，内含元素为`SymbolItem`的对象。

### 2. 全局变量

全局变量

## 问题

1. 在条件表达式中解释过，整个计算表达式的过程使用的值均为`i32`类型，而在br中需要一个`i1`类型的bool值，所以在每次br命令执行之前，需要把cond的返回值进行一个类型强制转换。zext只能进行i1到i32而不能反过来，所以使用一个`icmp ne`命令，将输入值与0进行比较，得到结果会返回一个`i1`类型的值，并且在不为0时返回`true`，0时返回`false`。

```python
FILE_OUT.write('%%x%d = icmp ne i32 %s, 0\n' %(LOC, res[0])
```

2. if-else的代码块结束后，函数不会自动跳转到接下来的语句，所以需要给后面的代码单独设置代码块和编号
