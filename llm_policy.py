import importlib.util
import json
import os


HAS_SMOLAGENTS = importlib.util.find_spec("smolagents") is not None
if HAS_SMOLAGENTS:
    from smolagents import CodeAgent, LiteLLMModel


class SmolAgentPolicy:
    """
    使用 smolagents 做高层决策：
    - action: "goal" 或 "frontier"
    - replan: true/false

    若 smolagents 不可用或输出不可解析，自动回退到规则策略。
    """

    def __init__(self):
        self.enabled = False
        self.agent = None

        model_id = os.getenv("SMOLAGENT_MODEL_ID", "openai/gpt-4o-mini")

        if HAS_SMOLAGENTS and os.getenv("USE_SMOLAGENT", "0") == "1":
            self.enabled = True
            model = LiteLLMModel(model_id=model_id)
            self.agent = CodeAgent(tools=[], model=model)

    def decide(self, state_summary, rule_need_replan):
        if not self.enabled or self.agent is None:
            return {
                "action": "goal",
                "replan": rule_need_replan,
                "reason": "fallback-rule",
            }

        prompt = (
            "你是无人机导航策略器。"
            "请基于状态给出JSON，不要输出多余文本。"
            "JSON schema: {\"action\":\"goal|frontier\",\"replan\":true|false,\"reason\":\"...\"}."
            f"状态: {json.dumps(state_summary, ensure_ascii=False)}"
            "约束: 若goal_path_exists=false，则action必须是frontier。"
        )

        try:
            raw = self.agent.run(prompt)
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned.replace("json", "", 1).strip()

            decision = json.loads(cleaned)
            action = decision.get("action", "goal")
            replan = bool(decision.get("replan", rule_need_replan))

            if action not in {"goal", "frontier"}:
                action = "goal"

            return {
                "action": action,
                "replan": replan,
                "reason": decision.get("reason", "smolagent"),
            }
        except Exception:
            return {
                "action": "goal",
                "replan": rule_need_replan,
                "reason": "fallback-on-error",
            }
