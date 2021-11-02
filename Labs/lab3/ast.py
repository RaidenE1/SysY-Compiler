class AstNode:
    def __init__(self, type = 'T', children = None, name = None, val = None):
        self.type = type
        self.name = name
        self.val = val
        if children:
            self.children = children
        else:
            self.children = []

    # def set_val(self, val):
    #     self.val = val

    # def set_name(self, name):
    #     self.name = name

    # def __str__(self):

    
