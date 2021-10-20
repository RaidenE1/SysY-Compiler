import sys


def checkNum(d):
    if d >= '0' and d <= '9':
        return True

def checkLetter(l):
    if (l >= 'a' and l <= 'z') or (l >= 'A' and l <= 'Z'):
        return True
    else:
        return False
    
def checkToken(t):
    identifiers = {
        '=' : 'Assign',
        ';' : 'Semicolon',
        '(' : 'LPar',
        ')' : 'RPar',
        '{' : 'LBrace',
        '}' : 'RBrace',
        '+' : 'Plus',
        '*' : 'Mult',
        '/' : 'Div',
        '<' : 'Lt',
        '>' : 'Gt',
        '==' : 'Eq',
        'if' : 'If',
        'else' : 'Else',
        'while' : 'While',
        'break' : 'Break',
        'continue' : 'Continue',
        'return' : 'Return'
    }
    if t in identifiers.keys():
        return identifiers[t]
    else:
        return None

def output(out, type):
    if type == "identifier":
        res = checkToken(out)
        if res:
            print(res)
        else:
            print("Ident(%s)" % (out))
    elif type == "num":
        print("Number(%s)" % (out))
    elif type == "token":
        print(checkToken(out))
    elif type == "Err":
        print("Err")
    else:
        print("Unknown type:", type)

def wordExcuter(word):
    cur_type = "null"
    queue = []
    for idx, char in enumerate(list(word)):
        if checkNum(char):
            if cur_type == "null" or cur_type == "num":
                queue.append(char)
                cur_type = "num"
            elif cur_type == "identifier":
                queue.append(char)
            else:
                output(''.join(queue), cur_type)
                cur_type = "num"
                queue = [char]
        elif checkLetter(char) or char == '_':
            if cur_type == "null" or cur_type == "identifier":
                cur_type = "identifier"
                queue.append(char)
            else:
                output(''.join(queue), cur_type)
                cur_type = "identifier"
                queue = [char]
        else:
            if checkToken(char):
                if cur_type == "null":
                    queue.append(char)
                    cur_type = "token"
                elif cur_type == "identifier" or cur_type == "num":
                    output(''.join(queue), cur_type)
                    cur_type = "token"
                    queue = [char]
                else:
                    temp = queue.copy()
                    temp += [char]
                    if checkToken(''.join(temp)):
                        queue.append(char)
                    else:
                        output(''.join(queue), cur_type)
                        cur_type = "token"
                        queue = [char]
            else:
                if cur_type == "token":
                    temp = queue.copy()
                    temp += [char]
                    if checkToken(''.join(temp)):
                        queue.append(char)
                    else:
                        if len(queue) != 0:
                            output(''.join(queue), cur_type)
                        output('', "Err")
                        return False
                else:
                    if len(queue) != 0:
                        output(''.join(queue), cur_type)
                    output('', "Err")
                    return False
    if len(queue) != 0:
        output(''.join(queue), cur_type)
    return True


def textExcuter(line):
    words = line.split()
    res = True
    while res and len(words) > 0:
        res = wordExcuter(words.pop(0))
    return res
        
        
def main(argv):
    path = argv[-1]
    # print(path)
    f = open(path, 'r')
    res = True
    for line in f:
        if res == False:
            break
        else:
            res = textExcuter(line)


if __name__ == "__main__":
    main(sys.argv)