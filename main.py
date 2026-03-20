import os
import random

from agent import NavigationAgent
from environment import Environment
from llm_policy import SmolAgentPolicy
from planner import AStarPlanner


def summarize_state(env, current_pos, goal_path, goal_risk, frontier_path, frontier_goal, tick):
    goal_exists = goal_path is not None
    frontier_exists = frontier_path is not None

    default_action = "goal"
    if not goal_exists and frontier_exists:
        default_action = "frontier"

    return {
        "tick": tick,
        "position": current_pos,
        "target": env.target,
        "explored_ratio": round(env.explored_ratio(), 3),
        "default_action": default_action,
        "goal": {
            "path_exists": goal_exists,
            "path_len": len(goal_path) if goal_exists else None,
            "risk": goal_risk,
        },
        "frontier": {
            "path_exists": frontier_exists,
            "path_len": len(frontier_path) if frontier_exists else None,
            "goal": frontier_goal,
        },
    }


def pick_path_by_action(decision_action, summary, goal_path, frontier_path):
    if decision_action == "frontier" and summary["frontier"]["path_exists"]:
        return frontier_path, "frontier"

    if summary["goal"]["path_exists"]:
        return goal_path, "goal"

    if summary["frontier"]["path_exists"]:
        return frontier_path, "frontier"

    return None, "none"


def build_demo_aerial_capture(size):
    """构造一个可复现实验用的“俯拍三维数据”样例。"""
    random.seed(7)
    height_grid = [[0.15 for _ in range(size)] for _ in range(size)]
    risk_grid = [[0.05 for _ in range(size)] for _ in range(size)]

    for x in range(3, min(8, size)):
        for y in range(4, min(12, size)):
            height_grid[x][y] = 3.4  # 高障碍群

    for y in range(1, size - 1):
        height_grid[size // 2][y] = 1.7  # 坡坎/泥泞带
        risk_grid[size // 2][y] = 0.72

    for x in range(max(0, size - 6), size - 1):
        for y in range(max(0, size - 6), size - 1):
            risk_grid[x][y] = max(risk_grid[x][y], 0.8)

    return height_grid, risk_grid


def main():
    env = Environment(size=20, vision_radius=2)

    use_aerial_3d = os.getenv("USE_AERIAL_3D", "0") == "1"
    if use_aerial_3d:
        h, r = build_demo_aerial_capture(env.size)
        env.load_from_aerial_3d(height_grid=h, risk_grid=r)
        print("已载入三维俯拍数据并完成障碍/危险识别。")
    else:
        env.generate_obstacles(40)
        env.generate_danger(120)

    current_pos = env.start
    trail = {current_pos}
    current_path = None

    policy = SmolAgentPolicy()

    max_ticks = 160

    env.reveal_from(current_pos)

    print("Initial Known Map:")
    env.print_map(path_marks=trail, agent_pos=current_pos, use_known=True)

    for tick in range(1, max_ticks + 1):
        if current_pos == env.target:
            print(f"\n[Tick {tick}] 到达目标点: {env.target}")
            break

        env.step_dynamic_danger(danger_add_prob=0.03, danger_remove_prob=0.015)
        env.reveal_from(current_pos)

        planner = AStarPlanner(env.known_grid, unknown_cost=3)
        agent = NavigationAgent(env, planner)

        rule_need_replan = agent.should_replan(current_path)

        goal_path, goal_risk = agent.plan_safe_path(current_pos, env.target)
        frontier_goal = agent.choose_frontier_goal(current_pos)
        frontier_path = planner.find_path(current_pos, frontier_goal) if frontier_goal else None

        summary = summarize_state(
            env,
            current_pos,
            goal_path,
            goal_risk,
            frontier_path,
            frontier_goal,
            tick,
        )

        decision = policy.decide(summary, rule_need_replan)
        selected_path, path_name = pick_path_by_action(
            decision["action"], summary, goal_path, frontier_path
        )

        if decision["replan"] or current_path is None:
            current_path = selected_path
            print(
                f"[Tick {tick}] 决策={path_name} replan={decision['replan']} "
                f"reason={decision['reason']} explored={summary['explored_ratio']} goal_risk={goal_risk}"
            )

        if current_path is None or len(current_path) < 2:
            print(f"\n[Tick {tick}] 无可行路径，任务失败。")
            break

        current_pos = current_path[1]
        trail.add(current_pos)
        current_path = current_path[1:]

        if tick % 10 == 0 or current_pos == env.target:
            print(f"\nKnown Map Snapshot @ Tick {tick}")
            env.print_map(path_marks=trail, agent_pos=current_pos, use_known=True)

    else:
        print("\n超过最大步数，任务结束。")

    if current_pos == env.target:
        print("\n任务结果：成功到达目标。")
    else:
        print("\n任务结果：未到达目标。")


if __name__ == "__main__":
    main()
