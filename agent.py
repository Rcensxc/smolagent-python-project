class NavigationAgent:

    def __init__(self, environment, planner):
        self.env = environment
        self.planner = planner

    def evaluate_path(self, path):
        """
        计算路径风险
        """

        risk = 0

        for x, y in path:

            if self.env.grid[x][y] == 2:  # 危险区域
                risk += 5 # 经过危险区域风险增加

        return risk

    def plan_safe_path(self):
        """
        决策函数
        """

        path = self.planner.find_path(
            self.env.start,
            self.env.target
        )

        if path is None:
            return None

        risk = self.evaluate_path(path)

        print("Path risk:", risk)

        if risk > 10:
            print("风险过高，重新规划：")

        return path