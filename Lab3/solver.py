#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from collections import deque


def solve_maze(width, height, start, exit_pos, grid):
    """
    Ищет кратчайший путь от start до exit_pos в лабиринте grid
    шириной width и высотой height.
    Возвращает список направлений ['U','R','D','L'] или None, если пути нет.
    """
    # Массив посещённых ячеек
    visited = [[False] * width for _ in range(height)]
    # Для восстановления пути: в prev[y][x] хранится кортеж (px,py,dir),
    # где (px,py) — предыдущая клетка, dir — шаг, который привёл в (x,y)
    prev = [[None] * width for _ in range(height)]

    # Возможные движения: вверх, вправо, вниз, влево
    # и соответствующие буквы для вывода
    directions = [
        (0, -1, 'U'),
        (1, 0, 'R'),
        (0, 1, 'D'),
        (-1, 0, 'L'),
    ]

    sx, sy = start
    ex, ey = exit_pos

    dq = deque()
    dq.append((sx, sy))
    visited[sy][sx] = True

    # BFS
    while dq:
        x, y = dq.popleft()
        if (x, y) == (ex, ey):
            break
        for dx, dy, dirc in directions:
            nx, ny = x + dx, y + dy
            # проверяем границы и стену ('1' — стена, '0' — свободно)
            if 0 <= nx < width and 0 <= ny < height \
                    and not visited[ny][nx] and grid[ny][nx] == '0':
                visited[ny][nx] = True
                prev[ny][nx] = (x, y, dirc)
                dq.append((nx, ny))

    # Если финиш не достигнут
    if not visited[ey][ex]:
        return None

    # Восстанавливаем путь, двигаясь от exit к start по ссылкам prev
    path = []
    cx, cy = ex, ey
    while (cx, cy) != (sx, sy):
        px, py, dirc = prev[cy][cx]
        path.append(dirc)
        cx, cy = px, py
    path.reverse()
    return path


def main():
    data = sys.stdin.read().strip().split()
    # первый рядок: width height
    width, height = map(int, data[:2])
    # второй: start x y
    sx, sy = map(int, data[2:4])
    # третий: exit x y
    ex, ey = map(int, data[4:6])
    # далее height строк по width символов
    raw = data[6:]
    grid = [list(raw[i]) for i in range(height)]

    path = solve_maze(width, height, (sx, sy), (ex, ey), grid)
    if path is None:
        print("No path found")
    else:
        # выводим сначала длину пути, затем саму строку команд
        print(len(path))
        print(''.join(path))


if __name__ == '__main__':
    main()
