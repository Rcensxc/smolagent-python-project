import random


UNKNOWN = -1


class Environment:

    def __init__(self, size=20, vision_radius=2):
        """
        环境包含：
        - true_grid: 真实地图（障碍/危险）
        - known_grid: 无人机已知地图（未知为 UNKNOWN）
        """
        self.size = size
        self.vision_radius = vision_radius

        self.true_grid = [[0 for _ in range(size)] for _ in range(size)]
        self.known_grid = [[UNKNOWN for _ in range(size)] for _ in range(size)]

        self.start = (0, 0)
        self.target = (size - 1, size - 1)

    def _is_protected_cell(self, x, y):
        return (x, y) == self.start or (x, y) == self.target

    def generate_obstacles(self, num=30):
        """随机生成障碍物（写入真实地图）"""
        for _ in range(num):
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self._is_protected_cell(x, y):
                self.true_grid[x][y] = 1

    def generate_danger(self, num=10):
        """随机生成危险区域（写入真实地图）"""
        for _ in range(num):
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self._is_protected_cell(x, y) and self.true_grid[x][y] == 0:
                self.true_grid[x][y] = 2

    def step_dynamic_danger(self, danger_add_prob=0.02, danger_remove_prob=0.01):
        """
        动态更新危险区（真实地图）：
        - 空地有概率变成危险区
        - 危险区有概率恢复为空地
        """
        for x in range(self.size):
            for y in range(self.size):
                if self._is_protected_cell(x, y) or self.true_grid[x][y] == 1:
                    continue

                if self.true_grid[x][y] == 0 and random.random() < danger_add_prob:
                    self.true_grid[x][y] = 2
                elif self.true_grid[x][y] == 2 and random.random() < danger_remove_prob:
                    self.true_grid[x][y] = 0

    def reveal_from(self, center_pos, radius=None):
        """根据无人机视野更新已知地图"""
        radius = self.vision_radius if radius is None else radius
        cx, cy = center_pos

        for x in range(max(0, cx - radius), min(self.size, cx + radius + 1)):
            for y in range(max(0, cy - radius), min(self.size, cy + radius + 1)):
                if abs(x - cx) + abs(y - cy) <= radius:
                    self.known_grid[x][y] = self.true_grid[x][y]

        # 始终确保起终点可见
        sx, sy = self.start
        tx, ty = self.target
        self.known_grid[sx][sy] = self.true_grid[sx][sy]
        self.known_grid[tx][ty] = self.true_grid[tx][ty]

    def explored_ratio(self):
        known = 0
        for row in self.known_grid:
            for v in row:
                if v != UNKNOWN:
                    known += 1
        return known / (self.size * self.size)

    def print_map(self, path_marks=None, agent_pos=None, use_known=True):
        symbols = {
            UNKNOWN: "?",
            0: ".",
            1: "X",
            2: "D",
            3: "*",
        }

        grid = self.known_grid if use_known else self.true_grid
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
                    row += symbols[grid[i][j]] + " "

            print(row)
