class AstNode:
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
