import random


class Environment:

    def __init__(self, size=20):
        """
        构造函数，环境类中的对象：size, 地图grid, 起点start, 终点target
        """
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.start = (0, 0)
        self.target = (size - 1, size - 1)

    def _is_protected_cell(self, x, y):
        return (x, y) == self.start or (x, y) == self.target

    def generate_obstacles(self, num=30):
        """随机生成障碍物"""
        for _ in range(num):
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self._is_protected_cell(x, y):
                self.grid[x][y] = 1

    def generate_danger(self, num=10):
        """随机生成危险区域"""
        for _ in range(num):
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self._is_protected_cell(x, y) and self.grid[x][y] == 0:
                self.grid[x][y] = 2

    def step_dynamic_danger(self, danger_add_prob=0.02, danger_remove_prob=0.01):
        """
        动态更新危险区：
        - 空地有概率变成危险区
        - 危险区有概率恢复为空地
        """
        for x in range(self.size):
            for y in range(self.size):
                if self._is_protected_cell(x, y) or self.grid[x][y] == 1:
                    continue

                if self.grid[x][y] == 0 and random.random() < danger_add_prob:
                    self.grid[x][y] = 2
                elif self.grid[x][y] == 2 and random.random() < danger_remove_prob:
                    self.grid[x][y] = 0

    def print_map(self, path_marks=None, agent_pos=None):
        symbols = {
            0: ".",
            1: "X",
            2: "D",
            3: "*",
        }
        path_marks = path_marks or set()

        for i in range(self.size):
            row = ""
            for j in range(self.size):
                if agent_pos is not None and (i, j) == agent_pos:
                    row += "A "
                elif (i, j) == self.start:
                    row += "S "
                elif (i, j) == self.target:
                    row += "T "
                elif (i, j) in path_marks:
                    row += symbols[3] + " "
                else:
                    row += symbols[self.grid[i][j]] + " "

            print(row)
