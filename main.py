from environment import Environment
from planner import AStarPlanner
from agent import NavigationAgent


def main():
    env = Environment(20)

    env.generate_obstacles(40)
    env.generate_danger(120)

    current_pos = env.start
    trail = {current_pos}
    current_path = None

    max_ticks = 120

    print("Initial Map:")
    env.print_map(path_marks=trail, agent_pos=current_pos)

    for tick in range(1, max_ticks + 1):
        if current_pos == env.target:
            print(f"\n[Tick {tick}] 到达目标点: {env.target}")
            break

        env.step_dynamic_danger(danger_add_prob=0.03, danger_remove_prob=0.015)

        planner = AStarPlanner(env.grid)
        agent = NavigationAgent(env, planner)

        need_replan = agent.should_replan(current_path)

        if need_replan:
            current_path, path_risk = agent.plan_safe_path(current_pos, env.target)
            print(f"[Tick {tick}] 重规划 -> path_risk={path_risk}")

        if current_path is None or len(current_path) < 2:
            print(f"\n[Tick {tick}] 无可行路径，任务失败。")
            break

        next_pos = current_path[1]
        current_pos = next_pos
        trail.add(current_pos)

        current_path = current_path[1:]

        if tick % 10 == 0 or current_pos == env.target:
            print(f"\nMap Snapshot @ Tick {tick}")
            env.print_map(path_marks=trail, agent_pos=current_pos)

    else:
        print("\n超过最大步数，任务结束。")

    if current_pos == env.target:
        print("\n任务结果：成功到达目标。")
    else:
        print("\n任务结果：未到达目标。")


if __name__ == "__main__":
    main()
