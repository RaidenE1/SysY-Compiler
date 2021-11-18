# Lab5 作用域与全局变量

> 编译原理第五次实验

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

  定义如下两个函数方便查找：

  ```python
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
  ```

  - `find_var_in_domain`是在作用域内寻找同名变量。
  - `find_var_cross_domain`是沿着作用域树的叶节点向上递归查找，直到找到定义或者查询到跟节点为止。
  - 二者均返回None(未找到)，或者定义的变量(SymbolItem类型)。

- item_tab代表变量表，储存在作用域内有效的局部变量，内含元素为`SymbolItem`的对象。

### 2. 全局变量

全局变量定义新的文法：

```python
def p_CompUnit(p):
    ''' CompUnit : MulDef '''
    p[0] = p[1]

def p_MulDef(p):
    ''' MulDef : Decl MulDef
               | FuncDef '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', [p[1], p[2]], 'MulDef')
```

对于全局变量的作用域和变量定义时，向过程传入参数glob，表示是否为全局变量的操作。

```python
def operate_exp(n, cur_domain, glob = False):
    global VALUE_MAP
    global FILE_OUT
    global LOC
    # ......
def LDR(n, ignore = False, cur_domain = None, glob = False):
    if n != None and n.type != 'T':
        global FILE_OUT
        global DOMAIN_LOC
        global LOC
        global GLOBAL_LOC
        # ......
```

~~是一个非常繁琐的过程~~。其中对于全局变量的定义，检查其中的变量是否为const，或者常数，如果为var则直接非0值返回。这里调用前面写好的，对于const类型变量的检查函数：

```python
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
```

对与`*Exp`节点，同样添加glob变量。如果是glob时，那么在表达式计算遇到`Ident`的时候，不去加载寄存器，而是在当前domain里寻找，然后直接输出item.val，确保以一个可以计算的值返回。

```python
if var.name == 'Ident':
  item = find_var_cross_domain(cur_domain, var.val)
  if not item:
    sys.exit(1)
    if glob: # *
      return item.val, False # *
    LOC += 1
    FILE_OUT.write('%%x%d = load i32, i32* %s\n' % (LOC - 1, item.loc))
    return '%x' + str(LOC - 1), False
```
