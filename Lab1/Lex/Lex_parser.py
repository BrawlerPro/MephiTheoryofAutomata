from parser import lexer

if __name__ == "__main__":
    with open("test.txt", "r") as f:
        test_cases = f.readlines()

    for case in test_cases:
        lexer(case)