import heapq

class AStarPlanner:

    def __init__(self, grid):
        self.grid = grid
        self.size = len(grid)

    def get_cost(self, x, y):

        if self.grid[x][y] == 0:  # 空地
            return 1

        if self.grid[x][y] == 2:  # 危险区域
            return 6

        return 1

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self, start, goal):

        open_list = []
        heapq.heappush(open_list, (0, start))

        came_from = {}

        g_score = {start: 0}

        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1)
        ]

        while open_list:

            current = heapq.heappop(open_list)[1]

            if current == goal:
                return self.reconstruct_path(came_from, current)

            for d in directions:

                neighbor = (
                    current[0] + d[0],
                    current[1] + d[1]
                )

                x, y = neighbor

                if not (0 <= x < self.size and 0 <= y < self.size):
                    continue

                if self.grid[x][y] == 1:
                    continue

                cost = self.get_cost(x, y)

                tentative_g = g_score[current] + cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g

                    f = tentative_g + self.heuristic(neighbor, goal)

                    heapq.heappush(open_list, (f, neighbor))

        return None

    def reconstruct_path(self, came_from, current):

        path = [current]

        while current in came_from:
            current = came_from[current]
            path.append(current)

        path.reverse()

        return path