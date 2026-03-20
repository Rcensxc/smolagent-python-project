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


def main():
    env = Environment(size=20, vision_radius=2)

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
