import sys

def main(argv):
    f = open(sys.argv[1])
    a, b = map(int, f.readline().split())
    print(a + b)




if __name__ == "__main__":
    main(sys.argv)