"""Interactive CLI for NBA data analyst agent."""

from src.agents.orchestrator import create_orchestrator


def main() -> None:
    print("=== NBA データアナリストエージェント ===")
    print("質問を入力してください。終了するには 'exit' または 'quit' を入力してください。\n")

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

        orchestrator = create_orchestrator()
        result = orchestrator(user_input)
        print(f"\nエージェント: {result}\n")


if __name__ == "__main__":
    main()
