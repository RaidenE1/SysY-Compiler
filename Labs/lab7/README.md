# Lab7 数组

> 编译原理第七次实验
>
> 18351015 张津赫

## 实验内容

- 本次实验结束后，编译器在 lab 6 的基础上支持一维数组和二维数组。

## 实现思路

在这次试验里直接实现了多维数组，可能还有一些bug，但是架构已经完善，后续修改一些逻辑问题即可。

涉及到数组的地方一共有三个：

- 变量定义
  - 常量数组
  - 变量数组
- 变量赋值
- 变量取值

***全部数组均采用一维数组进行模拟***



### 1. 数组定义

由文法可以看出，声明数组的节点是ConstArr或VarArr，所以在遍历到这两类节点时跳出，调用专门的数组解析函数arr_decl。

```python
def LDR(n, ignore = False, cur_domain = None, glob = False, condition = None, loc_break = None, loc_continue = None):
    if n != None and n.type != 'T':
        global FILE_OUT
        global DOMAIN_LOC
        global LOC
        global GLOBAL_LOC
        # ......
        if n.name == 'VarDecl':
            LDR(n.children[1], ignore, cur_domain, glob)
            return 
        elif n.name == 'ConstDecl':
            LDR(n.children[2], ignore, cur_domain, glob)
            return 
        elif n.name == 'VarArr' or n.name == 'ConstArr':
            arr_decl(n, cur_domain, glob)
            return
        # ......
```

arr_decl:

```python
def arr_decl(n, cur_domain, glob = False):
    global LOC
    global FILE_OUT
    global GLOBAL_LOC
    _name = n.children[0]
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
```

- _name 储存数组的变量名
- 使用check_val检查声明数据的大小的每一个变量必须是const，如果有var出现直接调用sys.exit(1)

- brackets代表连续的中括号，在数组定义阶段表示数组的大小。其中get_brackets(_brackets)返回 _brackets中每一对[，]中间的表达式

```python
def get_brackets(n):
    if len(n.children) == 3:
        return [n.children[1]]
    else:
        return [n.children[1]] + get_brackets(n.children[3])
      
#参照文法：
def p_AddBracket(p):
    ''' AddBracket : LBracket AddExp RBracket AddBracket
                   | LBracket AddExp RBracket '''
    p[0] = AstNode('NT', p[1:], 'AddBracket')
```

- 利用brackets为_brackets中每个表达式计算后的结果，用一个循环遍历检查，如果不是整形，那么说明返回了一个寄存器，即表达式无法在编译时求值，调用sys.exit(1)
- get_mul()用于计算数组容量:

```python
def get_mul(l):
    res = 1
    for i in l:
        assert isinstance(i, int)
        res *= i
    return res
```

- 同时还需要调用find_var_in_domain来检查_name是否已经被其他变量使用过

最后得到一个纬度为len(brackets)，每个维度的长度按顺序依次储存在brackets中的数组。

#### 1.1 常量数组

当node.name == 'ConstArr'时说明该节点是一个常量数组的声明。

- 首先常量数组的声明一定有值，所以调用get_init_val()获取一个装载初始值的列表：
  - 如果返回None说明遇到{}，*Exp节点则是一个值，返回。
  - 否则递归
- 其中取到的每个值，都建立了一个新的数据结构，p是在当前层的索引，pos是每一层的索引填入到这个列表中。

```python
class Array:
    def __init__(self, pos, val):
        self.pos = pos
        self.val = val
        
def get_add_init_val(n, p, pos, cur_domain, glob):
    res = get_init_val(n.children[1], 0, pos + [p], cur_domain, glob)
    if len(n.children) == 3:
        res += get_add_init_val(n.children[2], p + 1, pos, cur_domain, glob)
    return res

def get_init_val(n, p, pos, cur_domain, glob = False):
    if n.name[-3:] == "Exp":
        val = operate_exp(n, cur_domain, glob)[0]
        arr_node = Array(pos, val)
        return [arr_node]
    elif len(n.children) == 3:
        return get_init_val(n.children[1], 0, pos + [p], cur_domain, glob)
    elif len(n.children) == 4:
        return get_init_val(n.children[1], 0, pos + [p], cur_domain, glob) + get_add_init_val(n.children[2], 1, pos, cur_domain, glob)
    else:
        return None
      
# 参考文法：
def p_ConstInitVal(p):
    ''' ConstInitVal : AddExp 
                     | LBrace RBrace 
                     | LBrace ConstInitVal RBrace 
                     | LBrace ConstInitVal AddConstInitVal RBrace '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AstNode('NT', p[1:], 'ArrDecl')
        
def p_AddConstInitval(p):
    ''' AddConstInitVal : Comma ConstInitVal AddConstInitVal 
                        | Comma ConstInitVal '''
    if len(p) == 3:
        p[0] = AstNode('NT', [p[1], p[2]], 'AddConstInitVal')
    else:
        p[0] = AstNode('NT', [p[1], p[2], p[3]], 'AddConstInitVal')
```

- 根据参数glob来确定是否为全局数组，如果是全局数组则写法略有不同
- 如果为初值为{}，在全局数组中使用zeroinitializer，在局部数组中留到memset。
- 如果初值不为空，则遍历val_list里的每个值进行处理。

```python
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
```

- 对每一个 val_list中的val，首先利用pos列表求出转换成一维数组的位置。数组的dimL存有当时获取的每一个纬度的长度，相乘即可。
- 然后将计算的值，存在对应位置的数组指针里。

#### 1.2 变量数组

大体与常量数组定义相似，但因为常量数组允许声明而不定义初值，所以如果该节点的子节点数目为2的话则：

- 全局数组使用zeroinitializer
- 局部数组使用memset

```python
# 局部数组
item = SymbolItem('Var', 'Arr', _name, cur_domain, '%x'+str(LOC), arr_name, dim, brackets)
cur_domain.item_tab.append(item)
LOC += 1
FILE_OUT.write('%s = alloca %s\n' % (item.loc, item.val))
FILE_OUT.write('%%x%d = getelementptr %s, %s* %s' %(LOC, item.val, item.val, item.loc))
LOC += 1
FILE_OUT.write(', i32 0, i32 0\n')
FILE_OUT.write('call void @memset(i32* %%x%d,i32 %d,i32 %d)\n' % (LOC - 1, 0, 4*get_mul(brackets)))
```

### 2. 数组赋值

#### 2.1 常量数组

无论任何情况下对常量数组的赋值都是不允许的，所以直接调用sys.exit(1)即可

#### 2.2 变量数组

