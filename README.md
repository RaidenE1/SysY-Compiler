# SysY-Compiler

北京航空航天大学软件学院1921级编译原理课程实验

## 简介

本项目采用python语言编写，使用PLY进行词法分析和语法分析，构建的一种类C语言的编译器。只处理前端代码到LLVM IR的部分，目的是生成可以正确解释的LLVM IR文件。

实验要求参见[此处](https://github.com/BUAA-SE-Compiling/miniSysY-tutorial) 

评测机地址[戳戳](https://oj.karenia.cc/dashboard)

## 说明

- [src](./src/) 目录下是整个编译器完整的代码
- [libsysy](./libsysy/) 目录下是SysY语言需要链接的库
- 具体测试，包括`Dockerfile`和`judge.toml`的编写要求可以参照 [test](./test/) 目录下的说明
- 其中[Labs](./Labs/)目录下是每一次实验的代码，经过多次重构和迭代，功能可能有所重复，但可以对照实验需求观察迭代的过程。

代码结构：

```
├── src
   ├── main.py // 函数的入口以及主体部分，包括读取文件、处理代码、生成IR文件和输出
   ├── parser_modules.py // yacc的构建和语法规则
   ├── tokrules.py // 关于lexer识别token的正则表达式以及错误处理
   ├── ast_modules.py // 语法树的节点类
   ├── Dockerfile // 评测时构建镜像的依赖，参考 /test/ 下的说明
   ├── judge.toml // 测评的依据，参考 /test/ 下的说明
├── libsysy // 库函数
   ├── libsysy.c
   ├── libsysy.h
```

## 运行项目

## 环境配置

要运行本项目，首先要有 Python 环境，并安装 Ply 库:
```bash
pip install ply
```
推荐在 Ubuntu/MacOS 环境上执行，并安装 llvm 工具链。Ubuntu 20.04 的安装命令如下：
```bash
$ sudo apt-get install llvm
$ sudo apt-get install clang
```
安装完成后可以通过以下命令进行测试：

$ clang -v 		# 查看版本，若出现版本信息则说明安装成功
$ lli --version # 查看版本，若出现版本信息则说明安装成功

## 其他

课程大作业里面的Bug可能很多，代码写的也很乱，功能方面也不是十分完善，但之后不打算进行任何维护。

## 归档

- [pre-lab](./Labs/pre_lab) Accepted on Oct 3, 2021
- [lab1](./Labs/lab1/) Accepted on Oct 15, 2021
- [lab2](./Labs/lab2) Accepted on Oct 23, 2021
- [lab3](./Labs/lab3/) Accepted on Nov 5,2021
- [lab4](./Labs/lab4/) Accepted on Nov 9,2021
- [lab5](./Labs/lab5/) Accepted on Nov 18,2021
- [lab6](./Labs/lab6/) Accepted on Nov 19,2021
- [lab7](./Labs/lab7/) Accepted on Nov 23,2021
- [lab8](./Labs/lab8/)  Accepted on Nov 25,2021
- [challenge : Multi-dimensional array](./Labs/challenge/MDA/) Accepted on Dec 3,2021
- [challenge : Short-circuit evaluation](./Labs/challenge/SCE/) Accepted on Dec 3,2021

## 参考文档

PLY的说明文档参见[此处](http://www.dabeaz.com/ply/ply.html)

LLVM IR 参考:[LLVM Lang Ref](https://llvm.org/docs/LangRef.html) & [LLVM Programmer Manual](https://llvm.org/docs/ProgrammersManual.html)
