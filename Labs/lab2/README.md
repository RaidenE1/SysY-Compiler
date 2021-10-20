# Lab1 main与注释

> 编译原理第一次实验

## 实验内容

- 本次实验包括两个部分，需要完成一个简单的编译器，支持以下两个功能
    - 能够处理只包含一条 return 语句的 main 函数
    - 能够消除程序中的注释
    
    

## 实现思路

本次实验放弃了在`pre-lab`中定义好的词法分析器，而是采用了为python打造的语法分析器与词法分析器**PLY**，~~真是太好用了~~。可能工作量相比手写lexer和parser相比没什么区别，~~而且参考文档着实让我十分头秃~~

这里贴上[ply的文档](https://ply.readthedocs.io/en/latest/ply.html)



### 词法分析

大体的思路就是先定义好`ply.lex`需要的tokens和识别到tokens时对应的处理函数，~~这里写了一堆正则~~，根据ply文档所说，根据正则表达式从长到短安排token的处理顺序，可以有效避免一些如同`0x12(HEXADECIMAL)`被匹配成`0(OCTAL)`和`x(IDENT)`然后语法分析报错的bug。

在识别注释时使用正则应当注意最短匹配，~~(有一个点应该就是这样pf的)~~，就是说在遇到下面这种情况时，注释符号`(1)`应当匹配最近的注释符号`(2)`，而不是按照默认的贪婪规则去匹配注释符号`(4)`

```c
/*void                  //(1)
main */                 //(2)
return 0; /* return     //(3)
*/                      //(4)
```

开始的正则是：
```
'(//.*)|(/\*(.|\r\n|\n|\t\n)*\*/)'
```
修改之后：
```
'(//.*)|(/\*(.|\r\n|\n|\t\n)*?\*/)'
```
只差了一个`?`，因为`?`也是贪婪匹配，所以匹配到`*/`之后就会直接结束。



### 语法分析

语法分析只能说是很常规了，助教写好了语法，直接换成ply支持的解析函数格式就好了,~~自以为为了可拓展性所以把规则都拆开写了~~

```python
def p_Parser_init(p):
    ''' CompUnit : FuncDef '''
    # p[0] = ['FuncDef', p[1]]
    
def p_FuncDef(p):
    ''' FuncDef : FuncType Ident LPar RPar Block'''
    # p[0] = [p[1], p[2], p[3], p[4], p[5]]

def p_FuncType(p):
    ''' FuncType : Int '''
    # p[0] = [p[1], p.lineno(1)]

def p_Ident(p):
    ''' Ident : Main '''
    # p[0] = [p[1], p.lineno(1)]

def p_Block(p):
    ''' Block : LBrace Stmt RBrace '''
    # p[0] = [[p[1], p.lineno(1)], p[2], [p[3], p.lineno(3)]]  

def p_Stmt(p):
    ''' Stmt : Return Number Semicolon '''
    # p[0] = [[p[1], p.lineno(1)], [p[2], p.lineno(2)], [p[3], p.lineno(3)]]

def p_Number(p):
    ''' Number  : DECIMAL 
                | OCTAL 
                | HEXADECIMAL '''
    # p[0] = [p[1], p.lineno(1)]

def p_error(p):
    sys.exit(1)
    # print("Error de sintaxis", p)
    # print("Error en linea: "+ str(p.lineno))
```



### 其他的工作

因为`lexer`在`parser.parse()`的循环中会读取完所有token，所以在语法分析结束之后准备转换成`LLVM IR`的时候，需要一个之前深拷贝过的`lexer`，可以调用`ply.lex.py`内定义的`lex.clone()`函数。
