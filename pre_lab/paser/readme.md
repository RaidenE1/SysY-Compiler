# Lab Paser



## 1.实验内容

详情可见[paser指南](https://buaa-se-compiling.github.io/miniSysY-tutorial/pre/lab_parser.html)



## 2.实现思路

根据命令行输入的文件地址打开文件，然后按行读取，对于每一行利用split函数分成不同字符串。

对于每一个字符串，分字母读取到栈中，如果后读取的字符与前面的字符不能组成有效的token，则把栈中现有的合法token输出，然后检查新的字符，如果合法则留在栈内，否则直接报Err。

这种写法是为了在遇到文法中存在二义性的情况时（如 === 可以被识别成 Assign\nEq、Eq\nAssign 或 Assign\nAssign\nAssign），默认遵循最长匹配原则，即要尽可能多地识别一个 token 可以接受的字符。对于 ===，应识别成 Eq\nAssign。

