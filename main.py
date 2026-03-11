"""
from environment import Environment

env = Environment(20)

env.generate_obstacles(40)
env.generate_danger(15)

env.print_map()
"""
from environment import Environment
from planner import AStarPlanner

env = Environment(20)

env.generate_obstacles(40)
env.generate_danger(15)

planner = AStarPlanner(env.grid)

path = planner.find_path(env.start, env.target)

env.print_map()

print("\nPath:", path)
if path:
    for x, y in path:
        if (x, y) != env.start and (x, y) != env.target:
            env.grid[x][y] = "*"

env.print_map()
print("Path:", path)