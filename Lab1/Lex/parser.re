relations = {}

def register_relation(rel, attr):
    """Создаёт новое отношение с атрибутами."""
    if rel in attr:
        print(f"Ошибка: отношение {rel} уже существует!")
    else:
        relations[rel] = attr
        print(f"Создано отношение {rel} с атрибутами: {', '.join(attr)}")

def merge_relations(rel, relation1, relation2):
    """Создаёт новое отношение из двух других с объединением атрибутов."""
    if relation1 not in relations or relation2 not in relations:
        print(f"Ошибка: одно из отношений ({relation1}, {relation2}) не существует!")
    elif rel in relations:
        print(f"Ошибка: отношение {rel} уже существует!")
    else:
        merged_attributes = merge_attributes(relation1, relation2)
        relations[rel] = merged_attributes
        print(
            f"Создано отношение {rel} с объединёнными атрибутами: {', '.join(merged_attributes)}")

def merge_attributes(relation1, relation2):
    """Объединяет атрибуты двух отношений, избегая дубликатов."""
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

def parse_sql(text: str):
    # Подготовка входных данных
    yyinput = text.encode("ascii") + b"\0"
    yycursor = 0  # Индекс в строке

    # Метки для хранения индексов токенов
%{mtags format = '\n    @@ = []'; %}

%{
    re2c:YYMTAGP = "@@.append(yycursor)";
    re2c:YYMTAGN = ""; // Ничего не делаем
    re2c:yyfill:enable = 0;
    re2c:indent:top = 1;
    re2c:tags = 1;

    space = [ \t\n]+;
    identifier = [a-zA-Z_][a-zA-Z0-9_.]*;
    keyword_create = "create";
    keyword_as = "as";
    keyword_join = "join";
    lparen = "(";
    rparen = ")";
    comma = ",";

    keyword_create space* @rel_name_start identifier @rel_name
    (space* lparen space* @attr_start identifier (space* comma space* identifier)* @attr_end space* rparen)?
    (space* keyword_as space* @rel_name1_start identifier @rel_name1_end space* keyword_join space* @rel_name2_start identifier @rel_name2_end)? {
        relation = text[rel_name_start:rel_name] if rel_name_start else None
        relation1 = text[rel_name1_start:rel_name1_end] if rel_name1_start else None
        relation2 = text[rel_name2_start:rel_name2_end] if rel_name2_start else None
        attributes = []
        if attr_start is not None:
            attributes = [i.strip() for i in text[attr_start:attr_end].split(',') if i]

        if relation:
            if relation1 and relation2:
                merge_relations(relation, relation1, relation2)
            elif attributes:
                register_relation(relation, attributes)
            else:
                print("Ошибка: неверный SQL-запрос")
        return
    }


    * { print("Ошибка: неверный SQL-запрос"); return }
%}