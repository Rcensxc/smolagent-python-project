from environment import Environment
from planner import AStarPlanner
from agent import NavigationAgent
from llm_decider import LLMDecisionLayer


def mode_to_danger_cost(mode):
    if mode == "safe":
        return 10
    if mode == "fast":
        return 4
    return 6


def main():
    env = Environment(20)

    env.generate_obstacles(40)
    env.generate_danger(120)

    current_pos = env.start
    trail = {current_pos}
    current_path = None

    max_ticks = 120
    llm_layer = LLMDecisionLayer(enabled=True)

    print("Initial Map:")
    env.print_map(path_marks=trail, agent_pos=current_pos)
    if llm_layer.available:
        print("\nLLM 决策层状态: 已启用 (smolagents)")
    else:
        print("\nLLM 决策层状态: 不可用，自动使用规则兜底")

    for tick in range(1, max_ticks + 1):
        if current_pos == env.target:
            print(f"\n[Tick {tick}] 到达目标点: {env.target}")
            break

        env.step_dynamic_danger(danger_add_prob=0.03, danger_remove_prob=0.015)

        preview_planner = AStarPlanner(env.grid)
        preview_agent = NavigationAgent(env, preview_planner)
        path_risk = None
        danger_ahead = 0

        if current_path is not None and len(current_path) >= 2:
            path_risk = preview_agent.evaluate_path(current_path)
            danger_ahead = preview_agent.count_danger_ahead(current_path)

        decision = llm_layer.decide(
            tick=tick,
            current_pos=current_pos,
            target=env.target,
            path_risk=path_risk,
            danger_ahead=danger_ahead,
        )

        danger_cost = mode_to_danger_cost(decision["mode"])
        planner = AStarPlanner(env.grid, danger_cost=danger_cost)
        agent = NavigationAgent(env, planner)

        need_replan = decision["force_replan"] or agent.should_replan(
            current_path,
            risk_threshold=decision["risk_threshold"],
            danger_ahead_threshold=decision["danger_ahead_threshold"],
        )

        if need_replan:
            current_path, path_risk = agent.plan_safe_path(current_pos, env.target)
            print(
                f"[Tick {tick}] source={decision['source']} mode={decision['mode']} "
                f"replan=True path_risk={path_risk} reason={decision['reason']}"
            )
        else:
            print(
                f"[Tick {tick}] source={decision['source']} mode={decision['mode']} "
                "replan=False reason=沿用当前路径"
            )

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
