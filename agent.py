class NavigationAgent:

    def __init__(self, environment, planner):
        self.env = environment
        self.planner = planner

    def evaluate_path(self, path):
        """计算路径风险"""
        risk = 0
        for x, y in path:
            if self.env.grid[x][y] == 2:  # 危险区域
                risk += 5
        return risk

    def count_danger_ahead(self, path, lookahead=4):
        """统计前方若干步内危险格数量"""
        danger_count = 0
        for x, y in path[1 : lookahead + 1]:
            if self.env.grid[x][y] == 2:
                danger_count += 1
        return danger_count

    def should_replan(self, path, risk_threshold=20, lookahead=4, danger_ahead_threshold=2):
        """简单规则决策：路径风险高或前方危险过多则重规划"""
        if path is None or len(path) < 2:
            return True

        risk = self.evaluate_path(path)
        danger_ahead = self.count_danger_ahead(path, lookahead=lookahead)

        if risk > risk_threshold:
            return True

        if danger_ahead >= danger_ahead_threshold:
            return True

        return False

    def plan_safe_path(self, start, target):
        """从当前点到目标点进行规划"""
        path = self.planner.find_path(start, target)

        if path is None:
            return None, None

        risk = self.evaluate_path(path)
        return path, risk
