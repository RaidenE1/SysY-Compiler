class AstNode:
    def __init__(self, type = 'T', children = None):
        self.type = type
        if children:
            self.children = children
        else:
            self.children = []
