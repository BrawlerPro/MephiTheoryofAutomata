import random
import string


def random_name(min_length=1, max_length=10):
    first_char = random.choice(string.ascii_letters + "_")
    other_chars = ''.join(
        random.choices(string.ascii_letters + string.digits + "_.", k=random.randint(min_length - 1, max_length - 1)))
    return first_char + other_chars


def generate_correct_relation(existing_relations, name_length, attr_length, attr_count=3):
    relation = random_name(name_length, name_length)
    attributes = ', '.join(random_name(attr_length, attr_length) for _ in range(attr_count))
    existing_relations.add(relation)
    return f"create {relation} ({attributes})"


def generate_correct_join(existing_relations, name_length):
    if len(existing_relations) < 2:
        return generate_correct_relation(existing_relations, name_length, name_length)

    relation0 = random_name(name_length, name_length)
    relation1, relation2 = random.sample(list(existing_relations), 2)
    existing_relations.add(relation0)
    return f"create {relation0} as {relation1} join {relation2}"


def generate_incorrect(existing_relations, name_length, attr_length):
    error_type = random.choice(["bad_name", "missing_join", "empty_attributes"])
    if error_type == "bad_name":
        relation = random.choice([str(random.randint(0, 9)) + random_name(name_length, name_length), "!invalid_name"])
        attributes = ', '.join(random_name(attr_length, attr_length) for _ in range(random.randint(1, 5)))
        return f"create {relation} ({attributes})"
    elif error_type == "missing_join":
        relation0 = random_name(name_length, name_length)
        relation1 = random_name(name_length, name_length)
        return f"create {relation0} as {relation1} join"
    elif error_type == "empty_attributes":
        relation = random_name(name_length, name_length)
        return f"create {relation} ()"


def generate_samples(name_length, attr_length, correct_count=5, incorrect_count=5):
    existing_relations = set()
    correct_samples = [
        generate_correct_relation(existing_relations, name_length,
                                  attr_length) if random.random() < 0.5 else generate_correct_join(existing_relations,
                                                                                                   name_length)
        for _ in range(correct_count)
    ]
    incorrect_samples = [generate_incorrect(existing_relations, name_length, attr_length) for _ in
                         range(incorrect_count)]
    return correct_samples + incorrect_samples


if __name__ == "__main__":
    name_length = int(input("Введите длину имени отношения: "))
    attr_length = int(input("Введите длину атрибутов: "))
    correct_count = int(input("Введите количество корректных строк: "))
    incorrect_count = int(input("Введите количество некорректных строк: "))

    samples = generate_samples(name_length, attr_length, correct_count, incorrect_count)
    for s in samples:
        print(s)
