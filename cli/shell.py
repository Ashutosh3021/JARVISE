"""
JARVIS Interactive Shell
"""

from cli.client import JarvisClient


def simple_shell(client: JarvisClient):
    """Interactive shell — direct agent, no server."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                 JARVIS Interactive Shell                  ║
║                                                           ║
║  Commands:                                                ║
║    :help     - Show this help                            ║
║    :memory   - View recent memories                      ║
║    :stats    - Show system stats                         ║
║    :clear    - Clear conversation                        ║
║    :quit     - Exit shell                                ║
╚═══════════════════════════════════════════════════════════╝
""")

    print("JARVIS ready\n")

    messages = []

    while True:
        try:
            user_input = input("\n[You] ").strip()

            if not user_input:
                continue

            if user_input.startswith(":"):
                cmd = user_input[1:].strip().lower()

                if cmd == "help":
                    print("""
Commands:
  :help     - Show this help
  :memory   - View recent memories
  :stats    - Show system statistics
  :clear    - Clear conversation history
  :quit     - Exit shell
                    """)

                elif cmd in ("memory", "memories"):
                    print("\nFetching memories...")
                    result = client.get_memories(limit=10)
                    memories = result.get("memories", [])

                    if not memories:
                        print("No memories found")
                    else:
                        print(f"\n--- Recent Memories ({len(memories)}) ---")
                        for i, mem in enumerate(memories, 1):
                            query = mem.get("metadata", {}).get("user_query", str(mem))[:60]
                            print(f"{i}. {query}")

                elif cmd == "stats":
                    print("\nFetching system stats...")
                    result = client.get_stats()

                    cpu = result.get("cpu", {}).get("percent", "N/A")
                    mem = result.get("memory", {})
                    mem_used = mem.get("used_gb", "N/A")
                    mem_total = mem.get("total_gb", "N/A")
                    mem_pct = mem.get("percent", "N/A")

                    if isinstance(mem_used, (int, float)) and isinstance(mem_total, (int, float)):
                        print(f"\n  CPU:     {cpu}%")
                        print(f"  Memory:  {mem_used:.1f}GB / {mem_total:.1f}GB ({mem_pct}%)")
                    else:
                        print(f"\n  CPU:     {cpu}%")
                        print(f"  Memory:  {mem_used} / {mem_total} ({mem_pct}%)")

                elif cmd == "clear":
                    messages = []
                    print("Conversation cleared")

                elif cmd in ("quit", "exit"):
                    print("\nGoodbye!")
                    break

                else:
                    print(f"Unknown command: {cmd}")
                    print("Type :help for available commands")

                continue

            print("\n[JARVIS] ", end="", flush=True)
            response = client.chat(user_input)
            print(response)

            messages.append(("user", user_input))
            messages.append(("assistant", response))

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            break
