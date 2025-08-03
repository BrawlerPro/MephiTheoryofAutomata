# src/visualizer.py
import pygame
import sys


class Visualizer:
    def __init__(self, world_map, robot, exit_cell, cell_size=40, fps=5):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 48)

        self.world_map = world_map
        self.robot = robot
        self.exit = exit_cell  # tuple (x, y)
        self.cell = cell_size
        self.clock = pygame.time.Clock()
        self.fps = fps

        w, h = world_map.width, world_map.height
        self.screen = pygame.display.set_mode((w * cell_size, h * cell_size))
        pygame.display.set_caption("Cellular Robot Simulator")

    def draw(self):
        WHITE, BLACK, RED = (255, 255, 255), (0, 0, 0), (200, 50, 50)
        self.screen.fill(WHITE)

        # рисуем выход зелёным
        ex, ey = self.exit
        pygame.draw.rect(
            self.screen,
            (50, 200, 50),
            (ex * self.cell, ey * self.cell, self.cell, self.cell)
        )

        # рисуем стены
        for y in range(self.world_map.height):
            for x in range(self.world_map.width):
                if self.world_map.grid[y][x] == 1:
                    pygame.draw.rect(
                        self.screen, BLACK,
                        (x * self.cell, y * self.cell, self.cell, self.cell)
                    )

        # рисуем робота
        rx = self.robot.x * self.cell + self.cell // 2
        ry = self.robot.y * self.cell + self.cell // 2
        pygame.draw.circle(self.screen, RED, (rx, ry), self.cell // 3)

        pygame.display.flip()
        self.clock.tick(self.fps)

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def show_message(self, text):
        # полупрозрачный белый фон
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 200))
        self.screen.blit(overlay, (0, 0))

        # рендерим и центрируем текст
        surf = self.font.render(text, True, (0, 0, 0))
        rect = surf.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(surf, rect)

        pygame.display.flip()
