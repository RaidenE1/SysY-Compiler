class Compiler:
    def __init__(self, input_path, output_path):
        self.input_file = open(input_path, 'r')
        self.output_file = open(output_path, 'w')
        self.ident = ['main']
        self.func_type = ['int']
