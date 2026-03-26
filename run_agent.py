"""
Week 2 — CLI Entry Point
Run: py run_agent.py
"""

import sys
sys.path.insert(0, ".")

from agent.orchestrator import ask

BANNER = """
╔══════════════════════════════════════════════╗
║       Fleet Intelligence Agent  v0.1        ║
║  Type your question or 'exit' to quit       ║
╚══════════════════════════════════════════════╝
"""

DEMO_QUERIES = [
    "Which branches need the most urgent attention right now?",
    "Tell me everything about Reg_0289",
    "Are our highest fuel-cost vehicles also our highest risk?",
    "Give me a fleet health summary",
]


def main():
    print(BANNER)
    print("Demo queries to try:")
    for i, q in enumerate(DEMO_QUERIES, 1):
        print(f"  {i}. {q}")
    print()

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        print("\nAgent: thinking...\n")
        answer = ask(question, verbose=True)
        print(f"\nAgent:\n{answer}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
