"""エージェントの呼び出しトレースをターミナルに表示するモジュール。

Strands Agents の add_hook を使い、回答完了後に
オーケストレーター → サブエージェント → ツールの呼び出し階層を表示する。
"""

import json
from dataclasses import dataclass, field
from typing import Any

from strands import Agent
from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent

# ANSI カラーコード
_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_MAGENTA = "\033[95m"
_DIM = "\033[2m"


@dataclass
class _ToolCall:
    name: str
    input: Any
    output: Any = None


@dataclass
class _AgentTrace:
    name: str
    tool_calls: list[_ToolCall] = field(default_factory=list)


class AgentTracer:
    """エージェントのツール呼び出しを収集し、回答後にターミナルへ出力するトレーサー。"""

    def __init__(self) -> None:
        self._traces: list[_AgentTrace] = []
        self._current: dict[str, _AgentTrace] = {}
        self._pending: dict[str, _ToolCall] = {}

    def attach(self, agent: Agent) -> None:
        """指定エージェントにフックを登録する。"""
        agent.add_hook(self._before_tool, BeforeToolCallEvent)
        agent.add_hook(self._after_tool, AfterToolCallEvent)

    def _before_tool(self, event: BeforeToolCallEvent) -> None:
        agent_name = event.agent.name if hasattr(event, "agent") and event.agent else "unknown"
        if agent_name not in self._current:
            trace = _AgentTrace(name=agent_name)
            self._traces.append(trace)
            self._current[agent_name] = trace

        tool_use_id = event.tool_use.get("toolUseId", "")
        tool_name = event.tool_use.get("name", "")
        tool_input = event.tool_use.get("input", {})
        call = _ToolCall(name=tool_name, input=tool_input)
        self._current[agent_name].tool_calls.append(call)
        self._pending[tool_use_id] = call

    def _after_tool(self, event: AfterToolCallEvent) -> None:
        tool_use_id = event.tool_use.get("toolUseId", "")
        if tool_use_id in self._pending:
            result = event.result
            content = result.get("content", result) if isinstance(result, dict) else result
            self._pending[tool_use_id].output = content
            del self._pending[tool_use_id]

    def print_trace(self) -> None:
        """収集したトレースをターミナルに出力する。"""
        if not self._traces:
            return

        print(f"\n{_DIM}{'─' * 60}{_RESET}")
        print(f"{_BOLD}{_CYAN}📊 エージェント実行トレース{_RESET}")
        print(f"{_DIM}{'─' * 60}{_RESET}")

        for trace in self._traces:
            print(f"\n{_BOLD}{_MAGENTA}▶ Agent: {trace.name}{_RESET}")
            if not trace.tool_calls:
                print(f"  {_DIM}(ツール呼び出しなし){_RESET}")
                continue

            for i, call in enumerate(trace.tool_calls, 1):
                print(f"\n  {_BOLD}{_GREEN}[{i}] Tool: {call.name}{_RESET}")
                print(f"  {_YELLOW}Input:{_RESET}")
                print(_indent(_format_value(call.input), 4))
                print(f"  {_YELLOW}Output:{_RESET}")
                print(_indent(_format_value(call.output), 4))

        print(f"\n{_DIM}{'─' * 60}{_RESET}\n")

    def reset(self) -> None:
        """トレースをリセットする（次の会話ターンの前に呼ぶ）。"""
        self._traces.clear()
        self._current.clear()
        self._pending.clear()


def _format_value(value: Any) -> str:
    if value is None:
        return "(なし)"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
