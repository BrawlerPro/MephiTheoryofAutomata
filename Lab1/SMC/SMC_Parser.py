from Lab1.SMC.parser_sm import Parser_sm, StateMap


class SqlParser:
    def __init__(self):
        self.string = ""
        self.index = 0
        self.last_symbol = -1
        self.relations = {}  # Словарь для хранения отношений
        self.current_relation = None
        self.temp_relation1 = None
        self.temp_relation2 = None
        self.temp_attributes = []
        self.is_valid = False
        self._fsm = Parser_sm(self)

    def prepare(self, string: str):
        self.string = string
        self.index = 0
        self.current_relation = None
        self.temp_relation1 = None
        self.temp_relation2 = None
        self.temp_attributes.clear()
        self._fsm = Parser_sm(self)

    def peek(self) -> str:
        return self.string[self.index] if self.index < len(self.string) else "\n"

    def set_relation(self):
        self.current_relation = self.token_end()
        # print(self.current_relation)
        return self.current_relation

    def set_relation1(self):
        self.temp_relation1 = self.token_end()
        return self.temp_relation1

    def set_relation2(self):
        self.temp_relation2 = self.token_end()
        return self.temp_relation2

    def add_attribute(self):
        self.temp_attributes.append(self.token_end())
        return self.temp_attributes

    def consume_whitespace(self):
        while self.peek() == " ":
            self.consume()

    def match(self, keyword: str) -> bool:
        matched = keyword == self.string[self.index: self.index + len(keyword)]
        # print(f"Trying to match '{keyword}' at index {self.index}: {'Matched' if matched else 'Not Matched'}")
        return matched

    def consume(self, more=0):
        if self.index + more < len(self.string):
            # print(f"Consuming '{self.string[self.index]}' at index {self.index}, string: {self.string[self.index:]}")
            self.index += 1 + more

    def token_start(self):
        self.last_symbol = self.index - 1

    def token_end(self):
        token = self.string[self.last_symbol: self.index].strip()
        return token

    def register_relation(self):
        """Создаёт новое отношение с атрибутами."""
        if self.current_relation in self.relations:
            print(f"Ошибка: отношение {self.current_relation} уже существует!")
        else:
            self.relations[self.current_relation] = self.temp_attributes.copy()
            print(f"Создано отношение {self.current_relation} с атрибутами: {', '.join(self.temp_attributes)}")

    def merge_relations(self):
        """Создаёт новое отношение из двух других с объединением атрибутов."""
        if self.temp_relation1 not in self.relations or self.temp_relation2 not in self.relations:
            print(f"Ошибка: одно из отношений ({self.temp_relation1}, {self.temp_relation2}) не существует!")
        elif self.current_relation in self.relations:
            print(f"Ошибка: отношение {self.current_relation} уже существует!")
        else:
            merged_attributes = self.merge_attributes(self.temp_relation1, self.temp_relation2)
            self.relations[self.current_relation] = merged_attributes.copy()
            print(f"Создано отношение {self.current_relation} с объединёнными атрибутами: {', '.join(merged_attributes)}")

    def merge_attributes(self, relation1, relation2):
        """Объединяет атрибуты двух отношений, избегая дубликатов."""
        attributes1 = self.relations[relation1]
        attributes2 = self.relations[relation2]
        merged = []
        seen = {}

        for attr in attributes1 + attributes2:
            if attr in seen:
                new_attr = f"{seen[attr]}.{attr}"
            else:
                new_attr = attr
            merged.append(new_attr)
            seen[attr] = relation1 if attr in attributes1 else relation2

        return merged

    def acceptable(self):
        print("Valid SQL statement.")

    def unacceptable(self):
        print("Invalid SQL statement.")

    def next(self):
        self._fsm.next()

    def get_state(self):
        return self._fsm.getState()

    def is_finished(self) -> bool:
        return self.get_state() in {StateMap.unexpected, StateMap.end}


_parser = SqlParser()


def smc(text: str):
    _parser.prepare(text)
    while not _parser.is_finished():
        _parser.next()
    if _parser.get_state() == StateMap.unexpected:
        print("Invalid SQL statement.")
    if _parser.get_state() == StateMap.end:
        print("Valid SQL statement.")
    return _parser.relations


if __name__ == "__main__":
    with open("test.txt", "r") as f:
        test_cases = f.readlines()

    for case in test_cases:
        smc(case)

    print(_parser.relations)