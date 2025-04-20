import re
import sys

relations = {}  # Хранение созданных отношений и их атрибутов


def is_valid_create_relation(line: str):
    pattern = re.compile(r"""
        ^create\s+                                    # create + пробел
        (?P<relation>[a-zA-Z_][a-zA-Z0-9._]*)\s*      # имя_отношения
        \(\s*                                         # Открывающая скобка
        (?P<attributes>[a-zA-Z_][a-zA-Z0-9._]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9._]*)*)  # список атрибутов
        \s*\)$ # Закрывающая скобка
    """, re.VERBOSE)
    match = pattern.match(line)
    if match:
        return match.group("relation"), [attr.strip() for attr in match.group("attributes").split(',')]
    return None


def is_valid_create_join(line: str):
    pattern = re.compile(r"""
        ^create\s+                                 # create + пробел
        (?P<relation0>[a-zA-Z_][a-zA-Z0-9._]*)\s+  # имя_отношения_0
        as\s+                                      # as + пробел
        (?P<relation1>[a-zA-Z_][a-zA-Z0-9._]*)\s+  # имя_отношения_1
        join\s+                                    # join + пробел
        (?P<relation2>[a-zA-Z_][a-zA-Z0-9._]*)$    # имя_отношения_2
    """, re.VERBOSE)
    match = pattern.match(line)
    if match:
        return match.group("relation0"), match.group("relation1"), match.group("relation2")
    return None


def merge_attributes(relation1, relation2):
    attributes1 = relations[relation1]
    attributes2 = relations[relation2]
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


def regex(line: str):
    global relations
    result = ""
    relation_data = is_valid_create_relation(line)
    if relation_data:
        relation, attributes = relation_data
        if relation in relations:
            result = f"Ошибка: отношение {relation} уже существует!"
        else:
            relations[relation] = attributes
            result = f"Создано отношение {relation} со списком атрибутов: {', '.join(attributes)}"
    else:
        join_data = is_valid_create_join(line)
        if join_data:
            relation0, relation1, relation2 = join_data
            if relation1 not in relations or relation2 not in relations:
                result = f"Ошибка: одно из отношений ({relation1}, {relation2}) не существует!"
            elif relation0 in relations:
                result = f"Ошибка: отношение {relation0} уже существует!"
            else:
                merged_attributes = merge_attributes(relation1, relation2)
                relations[relation0] = merged_attributes
                result = f"Создано отношение {relation0} (объединение {relation1} и {relation2}) со списком атрибутов: {', '.join(merged_attributes)}"
        else:
            result = f"Некорректная строка: {line}"
    print(result)
    return relations


def main():
    with open("test.txt", "r") as f:
        test_cases = f.readlines()

    for case in test_cases:
        regex(case)


if __name__ == "__main__":
    main()
