import time
from Lab1.string_generator import generate_samples
from SMC_Parser import parse_sql


def measure_time(samples):
    results = []
    for line in samples:
        start_time = time.perf_counter()
        parse_sql(line)
        end_time = time.perf_counter()
        results.append(end_time - start_time)
    return sum(results)


def main():
    with open("results.txt", "w") as f:
        f.write("Correct Samples:\n")
        for _ in [10, 20, 50, 100, 500, 1000, 10000, 15000, 20000, 25000, 50000, 100000]:
            f.write(f"{_}:\n")
            f.write(f"SMC: {measure_time(generate_samples(_, _))}\n")

    print("Results saved in results.txt")


if __name__ == "__main__":
    main()
