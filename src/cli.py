"""Interactive CLI for NBA data analyst agent."""

from src.agents.data_agent import data_agent
from src.agents.analysis_agent import analysis_agent
from src.agents.orchestrator import create_orchestrator
from src.tracer import AgentTracer


def main() -> None:
    print("=== NBA データアナリストエージェント ===")
    print("質問を入力してください。終了するには 'exit' または 'quit' を入力してください。\n")

    tracer = AgentTracer()
    tracer.attach(data_agent)
    tracer.attach(analysis_agent)

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("終了します。")
            break

        tracer.reset()
        orchestrator = create_orchestrator()
        tracer.attach(orchestrator)
        result = orchestrator(user_input)
        print(f"\nエージェント: {result}\n")
        tracer.print_trace()


if __name__ == "__main__":
    main()
