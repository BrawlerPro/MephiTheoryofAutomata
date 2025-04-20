import matplotlib.pyplot as plt
import re

# Чтение файла
with open('results.txt', 'r') as file:
    data = file.read()

# Парсинг данных
sizes = []
regex_times = []
lexer_times = []
smc_times = []

# Регулярное выражение для извлечения чисел
pattern = re.compile(
    r'(\d+):\s*lexer:\s*([\d.e+-]+)\s*regex:\s*([\d.e+-]+)\s*smc:\s*([\d.e+-]+)'
)

matches = pattern.findall(data)
for match in matches:
    size = int(match[0])
    regex_time = float(match[2])
    lexer_time = float(match[1])
    smc_time = float(match[3])

    sizes.append(size)
    regex_times.append(regex_time)
    lexer_times.append(lexer_time)
    smc_times.append(smc_time)

# Построение графика
plt.figure(figsize=(10, 6))
plt.plot(sizes, regex_times, label='Regex', marker='o')
plt.plot(sizes, lexer_times, label='Lexer', marker='s')
plt.plot(sizes, smc_times, label='SMC', marker='^')

# Логарифмическая шкала (т.к. данные от 10 до 100000)
plt.xscale('log')
plt.yscale('log')

# Подписи
plt.xlabel('Размер входных данных (log scale)')
plt.ylabel('Время выполнения (секунды, log scale)')
plt.title('Сравнение производительности Regex, Lexer и SMC')
plt.legend()
plt.grid(True, which="both", ls="--")

# Сохранение графика
plt.savefig('results_plots.png')
plt.show()