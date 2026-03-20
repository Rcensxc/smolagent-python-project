class NavigationAgent:

    def __init__(self, environment, planner):
        self.env = environment
        self.planner = planner

    def evaluate_path(self, path):
        """计算路径风险（基于已知地图）"""
        risk = 0
        if path is None:
            return 10**9

        for x, y in path:
            cell = self.env.known_grid[x][y]
            if cell == 2:  # 危险区域
                risk += 5
            elif cell == -1:  # 未知区域
                risk += 2
        return risk

    def count_danger_ahead(self, path, lookahead=4):
        """统计前方若干步内危险格数量"""
        danger_count = 0
        if path is None:
            return danger_count

        for x, y in path[1: lookahead + 1]:
            if self.env.known_grid[x][y] == 2:
                danger_count += 1
        return danger_count

    def should_replan(self, path, risk_threshold=20, lookahead=4, danger_ahead_threshold=2):
        """规则决策：路径风险高或前方危险过多则重规划"""
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

    def find_frontiers(self):
        """Frontier: 已知可通行格，且邻居存在未知格"""
        size = self.env.size
        frontiers = []

        for x in range(size):
            for y in range(size):
                cell = self.env.known_grid[x][y]
                if cell in (1, -1):
                    continue

                neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                for nx, ny in neighbors:
                    if 0 <= nx < size and 0 <= ny < size and self.env.known_grid[nx][ny] == -1:
                        frontiers.append((x, y))
                        break

        return frontiers

    def choose_frontier_goal(self, current_pos):
        frontiers = self.find_frontiers()
        if not frontiers:
            return None

        tx, ty = self.env.target

        def score(pos):
            x, y = pos
            dist_to_target = abs(x - tx) + abs(y - ty)
            dist_to_current = abs(x - current_pos[0]) + abs(y - current_pos[1])
            return dist_to_target * 0.7 + dist_to_current * 0.3

        frontiers.sort(key=score)
        return frontiers[0]
