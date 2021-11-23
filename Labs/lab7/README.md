# Lab7 数组

> 编译原理第七次实验
>

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

### 1. 数组定义

由文法可以看出，声明数组的节点是`ConstArr`或`VarArr`，所以在遍历到这两类节点时跳出，调用专门的数组解析函数`arr_decl`。

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

`arr_decl`结构如下：

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

- `_name` 储存数组的变量名
- 使用`check_val`检查声明数据的大小的每一个变量必须是const，如果有var出现直接调用`sys.exit(1)`

- `brackets`代表连续的中括号，在数组定义阶段表示数组的大小。其中`get_brackets(_brackets)`返回 _brackets中每一对`[`，`]`中间的表达式

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

- 利用`brackets`储存`_brackets`中每个表达式计算后的结果，用一个循环遍历检查，如果不是整形，那么说明返回了一个寄存器，即表达式无法在编译时求值，调用`sys.exit(1)`
- `get_mul()`用于计算数组容量:

```python
def get_mul(l):
    res = 1
    for i in l:
        assert isinstance(i, int)
        res *= i
    return res
```

- 同时还需要调用`find_var_in_domain`来检查`_name`是否已经被其他变量使用过

最后得到一个纬度为`len(brackets)`，每个维度的长度按顺序依次储存在`brackets`中的数组。

#### 1.1 常量数组

当node.name == 'ConstArr'时说明该节点是一个常量数组的声明。

- 首先常量数组的声明一定有值，所以调用get_init_val()获取一个装载初始值的列表：
  - 如果返回`None`说明遇到`{}`，`*Exp`节点则是一个值，返回。
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

  - 全局数组声明时使用一个循环同时遍历整个数组和`val_list`，其中`arr_len`是通过`get_mul`获取的，模拟成一维数组的数组长度。通过val的pos列表和数组的维度列表可以知道当前val在目标一维数组中的索引
    - 如果`arr_ptr`和`val_ptr`相等，那么说明这个val应该在这里被声明。也只有这种情况下，`val_ptr`才向后移动一个。
    - 否则写入`i32 0`。
    - 无论两者任何一个没遍历结束都不应该停止循环，~~但实际上val_ptr不可能晚于arr_ptr，否则就是bug了~~

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

- 如果为初值为{}，在全局数组中使用`zeroinitializer`，在局部数组中留到`memset。`
- 如果初值不为空，则遍历val_list里的每个值进行处理。
- 对每一个 `val_list`中的val，首先利用`pos`列表求出转换成一维数组的位置。数组的`dimL`存有当时获取的每一个纬度的长度，相乘即可。
- 然后将计算的值，存在对应位置的数组指针里。

#### 1.2 变量数组

大体与常量数组定义相似，但因为常量数组允许声明而不定义初值，所以如果该节点的子节点数目为2的话则：

- 全局数组使用`zeroinitializer`
- 局部数组使用`memset`

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

- 首先调用find_val_cross_domain确认该数组被声明过

- 与声明时主要的区别在于brackets中可以含有无法直接求值的表达式，所以需要重新设计算法获取模拟成一维数组后元素的索引。思路如下：

  - 此时的表示索引的变量被存在寄存器中，每次的计算是一次乘法和一次加法:

    如取a\[1\]\[2\]的值，而a是3*4的数组，那么需要 `res = 0; res = res + (1 *4); res = res + 2;`

  - 然后将等号右侧的结果(由`operate_exp`获得)store在先前定义的索引中

```python
LOC += 2
res_pos_ptr = LOC - 2
res_pos = LOC - 1
FILE_OUT.write('%%x%d = alloca i32\nstore i32 0, i32* %%x%d\n%%x%d = load i32, i32* %%x%d\n' %(res_pos_ptr, res_pos_ptr, res_pos, res_pos_ptr))
changed = False
for idxx in range(len(brackets) - 1):
    val = brackets[idxx]
    if val != 0:
        LOC += 2
        FILE_OUT.write('%%x%d = mul i32 %s, %s\n' % (LOC - 2, val, item.dimL[idxx + 1]))
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
if len(brackets) == len(item.dimL):
    FILE_OUT.write(', i32 0')
FILE_OUT.write(', i32 %%x%d\n' % (res_pos))
FILE_OUT.write('store i32 %s, i32* %%x%d\n' % (res[0], LOC - 1))
```



### 3. 变量取值

当数组位于等号右侧的情况。且不区分常量与非常量数组。

思路与赋值时十分类似，是`operate_exp`中`PriExp`的一种子情况，唯一的区别是结束时需要返回寄存器的编号。

代码如下：

```python
if var.name == 'ArrVal':
    _brackets = get_brackets(var.children[1])
    brackets = [operate_exp(x, cur_domain, glob = False)[0] for x in _brackets]
    item = find_var_cross_domain(cur_domain, var.val)
    if not item:
        print('item not defined')
        sys.exit(1)
    LOC += 2
    res_pos_ptr = LOC - 2
    res_pos = LOC - 1
    FILE_OUT.write('%%x%d = alloca i32\nstore i32 0, i32* %%x%d\n%%x%d = load i32, i32* %%x%d\n' %(res_pos_ptr, res_pos_ptr, res_pos, res_pos_ptr))
    changed = False
    for idxx in range(len(brackets) - 1):
        val = brackets[idxx]
        if val != 0:
            LOC += 2
            FILE_OUT.write('%%x%d = mul i32 %s, %s\n' % (LOC - 2, val, item.dimL[idxx + 1]))
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
    if len(brackets) == len(item.dimL):
        FILE_OUT.write(', i32 0')
    FILE_OUT.write(', i32 %%x%d\n' % (res_pos))
    LOC += 1
    FILE_OUT.write('%%x%d = load i32, i32* %%x%d\n' % (LOC - 1, LOC - 2))
    return '%x' + str(LOC - 1), False
```

## 总结

为了后续的挑战实验方便，所以使用一维数组进行模拟，需要考虑的问题就是

1. 如何将一个多维数组的多维度索引转换成一维数组中的索引

   如果brackets代表数组的中括号包围的索引，dims代表数组的维度列表

   那么获取一维数组的索引应该是`sum(brackets[i] * dims[i + 1]) + brackets[-1]`

2. 一个测试点让我发现了我的`LAndExp`和`LOrExp`使用`i32`类型进行判断，而应该使用`i1`类型，需要一次强制转换。

   

   
