import random

class Environment:

    def __init__(self, size=20):#构造函数，self是对象本身，size为初始化参数
        """
        构造函数，环境类中的对象：size,地图grid,起点start,终点target
        """
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]#list[list[int]],组成一个二维数组
        self.start = (0, 0)
        self.target = (size-1, size-1)

    def generate_obstacles(self, num=30):
        """随机生成障碍物"""
        for _ in range(num):
            x = random.randint(0, self.size-1)
            y = random.randint(0, self.size-1)
            self.grid[x][y] = 1

    def generate_danger(self, num=10):
        """随机生成危险区域"""
        for _ in range(num):
            x = random.randint(0, self.size-1)
            y = random.randint(0, self.size-1)
            if self.grid[x][y] == 0:
                self.grid[x][y] = 2

    def print_map(self):

        symbols = {
            0: ".",
            1: "X",
            2: "D"
        }

        for i in range(self.size):
            row = ""
            for j in range(self.size):

                if (i, j) == self.start:
                    row += "S "
                elif (i, j) == self.target:
                    row += "T "
                else:
                    row += symbols[self.grid[i][j]] + " "

            print(row)