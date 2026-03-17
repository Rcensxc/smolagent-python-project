import json
import os
import re


class LLMDecisionLayer:
    """
    LLM 决策层：
    - 优先尝试使用 smolagents
    - 不可用时回退到规则策略，保证主程序可运行
    """

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.available = False
        self.error = None
        self.agent = None

        if not enabled:
            return

        try:
            from smolagents import CodeAgent, LiteLLMModel

            model_id = os.getenv("SMOLAGENTS_MODEL", "gpt-4o-mini")
            model = LiteLLMModel(model_id=model_id)
            self.agent = CodeAgent(tools=[], model=model)
            self.available = True
        except Exception as exc:
            self.error = str(exc)
            self.available = False

    @staticmethod
    def _extract_json(text):
        """从 LLM 返回文本中提取 JSON 块"""
        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            return text

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)

        return "{}"

    @staticmethod
    def _default_decision(path_risk, danger_ahead):
        """规则兜底策略"""
        if path_risk is None:
            return {
                "mode": "safe",
                "risk_threshold": 20,
                "danger_ahead_threshold": 2,
                "force_replan": True,
                "reason": "无路径，必须重规划",
                "source": "rule_fallback",
            }

        if path_risk > 30 or danger_ahead >= 3:
            return {
                "mode": "safe",
                "risk_threshold": 15,
                "danger_ahead_threshold": 1,
                "force_replan": True,
                "reason": "风险较高，切换安全模式",
                "source": "rule_fallback",
            }

        if path_risk > 15 or danger_ahead >= 2:
            return {
                "mode": "balanced",
                "risk_threshold": 20,
                "danger_ahead_threshold": 2,
                "force_replan": True,
                "reason": "风险中等，保持平衡并重规划",
                "source": "rule_fallback",
            }

        return {
            "mode": "fast",
            "risk_threshold": 30,
            "danger_ahead_threshold": 3,
            "force_replan": False,
            "reason": "风险较低，保持当前路径",
            "source": "rule_fallback",
        }

    def decide(self, tick, current_pos, target, path_risk, danger_ahead):
        """
        返回决策字典：
        {
          mode: safe|balanced|fast,
          risk_threshold: int,
          danger_ahead_threshold: int,
          force_replan: bool,
          reason: str,
          source: llm|rule_fallback
        }
        """
        fallback = self._default_decision(path_risk, danger_ahead)

        if not self.available:
            return fallback

        prompt = (
            "你是地震救援无人机的调度决策器。"
            "请根据状态给出决策，并只返回 JSON。"
            "JSON schema: "
            "{\"mode\":\"safe|balanced|fast\","
            "\"risk_threshold\":int,"
            "\"danger_ahead_threshold\":int,"
            "\"force_replan\":bool,"
            "\"reason\":\"...\"}.\n"
            f"tick={tick}, current_pos={current_pos}, target={target}, "
            f"path_risk={path_risk}, danger_ahead={danger_ahead}."
        )

        try:
            raw = self.agent.run(prompt)
            raw_json = self._extract_json(str(raw))
            data = json.loads(raw_json)

            mode = data.get("mode", fallback["mode"])
            if mode not in {"safe", "balanced", "fast"}:
                mode = fallback["mode"]

            decision = {
                "mode": mode,
                "risk_threshold": int(data.get("risk_threshold", fallback["risk_threshold"])),
                "danger_ahead_threshold": int(
                    data.get("danger_ahead_threshold", fallback["danger_ahead_threshold"])
                ),
                "force_replan": bool(data.get("force_replan", fallback["force_replan"])),
                "reason": str(data.get("reason", "")) or fallback["reason"],
                "source": "llm",
            }

            return decision
        except Exception:
            return fallback
