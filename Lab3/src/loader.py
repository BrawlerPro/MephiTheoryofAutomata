# src/loader.py

"""
loader.py — модуль для загрузки лабиринта и создания объектов WorldMap и Robot.

Формат входного файла лабиринта (plain text):
    # Первая строка: ширина и высота (W H), разделённые пробелом
    W H
    # Вторая строка: стартовые координаты робота (x y)
    start_x start_y
    # Третья строка: координаты выхода (x y)
    exit_x exit_y
    # Далее H строк — описание строк сетки:
    # каждая строка ровно W символов '0' (свободно) или '1' (преграда)
    row0
    row1
    …
    rowH-1

Координаты (0,0) — верхний-левый угол, x — вправо, y — вниз.
"""


class WorldMap:
    def __init__(self, width: int, height: int, grid: list[list[bool]], exit_pos: tuple[int, int]):
        self.width = width
        self.height = height
        self.grid = grid  # grid[y][x] == True ⇔ препятствие
        self.exit = exit_pos  # (exit_x, exit_y)

    def bar(self, x: int, y: int) -> bool:
        """Есть ли препятствие в (x,y)? Вне границ также считается препятствием."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True
        return self.grid[y][x]

    def emp(self, x: int, y: int) -> bool:
        """Пустая ли клетка?"""
        return not self.bar(x, y)

    def set_cell(self, x: int, y: int, val: bool = True) -> None:
        """Установить препятствие (val=True) или свободную клетку (val=False)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = val

    def clr(self, x: int, y: int) -> None:
        """Сбросить cell в свободное состояние."""
        self.set_cell(x, y, val=False)


class Robot:
    # смещения по направлениям: (dx, dy)
    DIR_DELTAS = {
        'NORTH': (0, -1),
        'SOUTH': (0, 1),
        'EAST': (1, 0),
        'WEST': (-1, 0),
    }
    # вращение
    RIGHT_TURN = {'NORTH': 'EAST', 'EAST': 'SOUTH', 'SOUTH': 'WEST', 'WEST': 'NORTH'}
    LEFT_TURN = {'NORTH': 'WEST', 'WEST': 'SOUTH', 'SOUTH': 'EAST', 'EAST': 'NORTH'}
    BACK_TURN = {'NORTH': 'SOUTH', 'SOUTH': 'NORTH', 'EAST': 'WEST', 'WEST': 'EAST'}

    def __init__(self, world_map: WorldMap, start_x: int, start_y: int):
        self.map = world_map
        self.x = start_x
        self.y = start_y
        self.orientation = 'NORTH'

    def step(self, direction: str) -> bool:
        """
        Переместиться на одну клетку в указанном (абсолютном) направлении.
        Если путь заблокирован или вне границ — не двигаться и вернуть False.
        Иначе — обновить позицию, orientation=direction, вернуть True.
        """
        dir_u = direction.upper()
        if dir_u not in self.DIR_DELTAS:
            raise ValueError(f"Unknown direction '{direction}'")
        dx, dy = self.DIR_DELTAS[dir_u]
        new_x = self.x + dx
        new_y = self.y + dy
        if self.map.bar(new_x, new_y):
            return False
        self.x, self.y = new_x, new_y
        self.orientation = dir_u
        return True

    def back(self) -> bool:
        """Повернуться на 180° относительно текущей ориентации."""
        self.orientation = self.BACK_TURN[self.orientation]
        return True

    def right(self) -> bool:
        """Повернуться на 90° вправо относительно текущей ориентации."""
        self.orientation = self.RIGHT_TURN[self.orientation]
        return True

    def left(self) -> bool:
        """Повернуться на 90° влево относительно текущей ориентации."""
        self.orientation = self.LEFT_TURN[self.orientation]
        return True

    def look(self) -> int:
        """
        Посчитать количество свободных клеток по текущему направлению
        до ближайшего препятствия (либо границы → считается препятствием).
        """
        dx, dy = self.DIR_DELTAS[self.orientation]
        cx, cy = self.x + dx, self.y + dy
        count = 0
        # пока внутри и без препятствия — считаем
        while 0 <= cx < self.map.width and 0 <= cy < self.map.height and not self.map.bar(cx, cy):
            count += 1
            cx += dx
            cy += dy
        return count


def load_labyrinth(path: str) -> tuple[WorldMap, Robot]:
    """
    Читает файл path в формате, описанном выше,
    возвращает (world_map, robot).
    """
    with open(path, 'r', encoding='utf-8') as f:
        # игнорируем пустые и комментированные строки
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith('#')]

    if len(lines) < 3:
        raise ValueError("Некорректный файл лабиринта: должно быть минимум 3 непустые строки")

    # 1) размеры
    w_str, h_str = lines[0].split()
    width, height = int(w_str), int(h_str)

    # 2) стартовая позиция
    sx_str, sy_str = lines[1].split()
    start_x, start_y = int(sx_str), int(sy_str)

    # 3) позиция выхода (можно сохранять, но пока не используется)
    ex_str, ey_str = lines[2].split()
    exit_x, exit_y = int(ex_str), int(ey_str)

    # 4) строки сетки
    grid_lines = lines[3:]
    if len(grid_lines) != height:
        raise ValueError(f"Expected {height} rows of map data, got {len(grid_lines)}")

    grid: list[list[bool]] = []
    for row in grid_lines:
        if len(row) != width:
            raise ValueError(f"Each map row must have width {width}, but got '{row}'")
        grid.append([c == '1' for c in row])

    world_map = WorldMap(width, height, grid, exit_pos=(exit_x, exit_y))
    robot = Robot(world_map, start_x, start_y)
    return world_map, robot
