from Lab1.RegEx.Regex_Parser import regex
from Lab1.Lex.parser import lexer
from Lab1.SMC.SMC_Parser import smc


def process_with_parser(parser_func, input_str):
    try:
        result = parser_func(input_str)
        print(result)
    except Exception as e:
        print("Ошибка:", e)


def main():
    parsers = {
        "1": ("Regex", regex),
        "2": ("Lexer", lexer),
        "3": ("SMC", smc),
    }

    while True:
        print("\nВыберите распознаватель:")
        for k, (name, _) in parsers.items():
            print(f"{k}. {name}")
        choice = input("Ваш выбор (или 'q' для выхода): ").strip()

        if choice.lower() == 'q':
            break

        if choice not in parsers:
            print("Неверный выбор.")
            continue

        _, parser = parsers[choice]

        input_mode = input("Ввести строку (1) или прочитать из файла (2)? ").strip()
        if input_mode == '1':
            input_str = input("Введите строку: ")
        elif input_mode == '2':
            file_path = input("Введите путь к файлу: ")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    input_str = f.read()
            except FileNotFoundError:
                print("Файл не найден.")
                continue
        else:
            print("Неверный режим.")
            continue

        process_with_parser(parser, input_str)


if __name__ == "__main__":
    main()
