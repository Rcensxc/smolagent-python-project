import importlib.util
import json
import os
from typing import Any, Dict


HAS_SMOLAGENTS = importlib.util.find_spec("smolagents") is not None
if HAS_SMOLAGENTS:
    from smolagents import CodeAgent, LiteLLMModel


class SmolAgentPolicy:
    """基于 smolagents 的高层策略器（可选启用）。"""

    def __init__(self):
        self.enabled = False
        self.agent = None

        model_id = os.getenv("SMOLAGENT_MODEL_ID", "openai/gpt-4o-mini")
        use_smolagent = os.getenv("USE_SMOLAGENT", "0") == "1"

        if HAS_SMOLAGENTS and use_smolagent:
            model = LiteLLMModel(model_id=model_id)
            self.agent = CodeAgent(tools=[], model=model)
            self.enabled = True

    def _fallback(self, state_summary: Dict[str, Any], rule_need_replan: bool, reason: str):
        default_action = state_summary.get("default_action", "goal")
        return {
            "action": default_action,
            "replan": rule_need_replan,
            "reason": reason,
        }

    def _build_prompt(self, state_summary: Dict[str, Any]) -> str:
        return (
            "你是无人机实时导航决策器。\n"
            "你的任务：在每个 tick 输出一个 JSON 决策。\n"
            "只输出 JSON，不要输出 markdown 或解释。\n"
            "\n"
            "决策规则：\n"
            "1) action 只能是 goal 或 frontier。\n"
            "2) 若 goal.path_exists=false，则 action 必须为 frontier。\n"
            "3) 若两者都不可用，保持默认 action。\n"
            "\n"
            "输出 schema：\n"
            "{\"action\": \"goal|frontier\", \"replan\": true|false, \"reason\": \"简短原因\"}\n"
            "\n"
            f"当前状态：{json.dumps(state_summary, ensure_ascii=False)}"
        )

    def _extract_json(self, raw: str):
        text = raw.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            text = text.replace("json", "", 1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found")
        return json.loads(text[start : end + 1])

    def decide(self, state_summary: Dict[str, Any], rule_need_replan: bool):
        if not self.enabled or self.agent is None:
            return self._fallback(state_summary, rule_need_replan, "fallback-rule")

        prompt = self._build_prompt(state_summary)

        try:
            raw = self.agent.run(prompt)
            parsed = self._extract_json(raw)

            action = parsed.get("action", state_summary.get("default_action", "goal"))
            replan = parsed.get("replan", rule_need_replan)
            reason = parsed.get("reason", "smolagent")

            if action not in {"goal", "frontier"}:
                action = state_summary.get("default_action", "goal")

            if action == "goal" and not state_summary.get("goal", {}).get("path_exists", False):
                action = "frontier"

            if action == "frontier" and not state_summary.get("frontier", {}).get("path_exists", False):
                action = state_summary.get("default_action", "goal")

            return {
                "action": action,
                "replan": bool(replan),
                "reason": str(reason),
            }
        except Exception:
            return self._fallback(state_summary, rule_need_replan, "fallback-on-error")
