# SysY-Compiler


> 北京航空航天大学软件学院1921级编译原理课程实验

实验要求参见[此处](https://github.com/BUAA-SE-Compiling/miniSysY-tutorial) 
评测机地址[戳戳](https://oj.karenia.cc/dashboard)

本项目采用python语言编写，使用PLY进行词法分析和语法分析，PLY的说明参见[此处](http://www.dabeaz.com/ply/ply.html)。使用手写的AST，~~不太成熟~~。并且只处理前端代码到LLVM IR的部分，目的是生成可以正确编译的IR文件。

代码结构：

```
├── src
   ├── main.py // 函数的入口以及主体部分，包括读取文件、处理代码、生成IR文件和输出
   ├── parser_modules.py // yacc的构建和语法规则
   ├── tokrules.py // 关于lexer识别token的正则表达式以及错误处理
   ├── ast_modules.py // 语法树的节点类
   ├── Dockerfile // 评测时构建镜像的依赖，参考 /test/ 下的说明
   ├── judge.toml // 测评的依据，参考 /test/ 下的说明
   
```

参考运行命令：

```bash
python main.py testin.in testout.ll //生成LLVM IR文件
lli testout.ll
```



## 说明

- [src](./src/) 目录下是整个编译器完整的代码
- 具体测试，包括`Dockerfile`和`judge.toml`的编写要求可以参照 [test](./test/) 目录下的说明
- 其中[Labs](./Labs/)目录下是每一次实验的代码，经过多次重构和迭代，功能可能有所重复，但可以对照实验需求观察迭代的过程。

## 归档

- [pre-lab](./Labs/pre_lab) Accepted on Oct 3, 2021
- [lab1](./Labs/lab1/) Accepted on Oct 15, 2021
- [lab2](./Labs/lab2) Accepted on Oct 23, 2021
- [lab3](./Labs/lab3/) Accepted on Nov 5,2021
- [lab4](./Labs/lab4/) Accepted on Nov 9,2021
- [lab5](./Labs/lab5/) yet to come ......

