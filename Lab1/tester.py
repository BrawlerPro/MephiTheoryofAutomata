import time
from string_generator import generate_samples
from Lab1.RegEx.Regex_Parser import regex as rpl
from Lab1.Lex.parser import lexer as lpl
from Lab1.SMC.SMC_Parser import smc as sml


def measure_time(samples, func):
    results = []
    for line in samples:
        start_time = time.perf_counter()
        func(line)
        end_time = time.perf_counter()
        results.append(end_time - start_time)
    return sum(results)


def main():
    with open("results.txt", "w") as f:
        f.write("Correct Samples:\n")
        for _ in [10, 20, 50, 100, 500, 1_000, 10_000, 25_000, 50_000, 100_000, 1_000_000, 5_000_000]:
            f.write(f"{_}:\n")
            for i in [lpl, rpl, sml]:
                f.write(f"{i.__name__}: {measure_time(generate_samples(_, 10, 1, 1), i)}\n")

    print("Results saved in results.txt")


if __name__ == "__main__":
    main()
