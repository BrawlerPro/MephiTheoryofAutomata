import pytest
from Lab3.src.loader import load_labyrinth, WorldMap, Robot
import tempfile

LAB_CONTENT = """\
3 2
1 1
2 0
010
101
"""


def test_load_labyrinth(tmp_path):
    f = tmp_path / "lab.lab"
    f.write_text(LAB_CONTENT)
    wm, robot = load_labyrinth(str(f))
    # Проверяем размеры и препятствия
    assert isinstance(wm, WorldMap)
    assert wm.width == 3 and wm.height == 2
    assert wm.bar(0, 0) is False
    assert wm.bar(1, 0) is True
    # Позиция робота
    assert isinstance(robot, Robot)
    assert (robot.x, robot.y) == (1, 1)
    # Выход
    assert wm.exit == (2, 0)
