
class AstNode: # 抽象语法树节点
    def __init__(self, type = 'T', children = None, name = None, val = None, const = True, loc = 0):
        self.type = type
        self.name = name
        self.val = val
        self.const = const
        self.loc = loc
        if children:
            self.children = children
        else:
            self.children = []

class SymbolItem: # 符号表
    def __init__(self, _type, dataType, name, domain, loc, val = None, dims = 0, dimL = [], typel = [], params = []):
        self._type = _type # ID类型，变量，数组，函数
        self.dataType = dataType
        self.name = name # ID名字
        self.domain = domain
        self.loc = loc
        self.val = val
        self.dim = dims
        self.dimL = dimL
        self.typel = typel
        self.params = params
        # self.arrayLen = arrayLen # 数组长度
        # self.args = args # 函数参数列表
        # self.returnType = returnType # 函数返回值类型
        # self.codeNum = codeNum # 四元式开始的位置

class Domain: # 作用域
    def __init__(self, num, children = None, father = None):
        self.num = num
        if not children:
            self.children = []
        else:
            self.children = children
        self.father = father
        self.item_tab = []

class Array:
    def __init__(self, pos, val):
        self.pos = pos
        self.val = val