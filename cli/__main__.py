"""
JARVIS CLI — Command-line interface.

Usage:
    jarvis chat "Hello, how are you?"
    jarvis shell
    jarvis memory list
    jarvis memory search "python"
    jarvis stats
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.client import JarvisClient
from cli.shell import simple_shell
from cli.display import display_chat, display_memory, display_stats, display_error


def main():
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS AI Assistant — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jarvis chat "Hello, how are you?"
  jarvis shell
  jarvis memory list
  jarvis memory search "query"
  jarvis stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    chat_parser = subparsers.add_parser("chat", help="Send a message to JARVIS")
    chat_parser.add_argument("message", nargs="*", help="Message to send")

    subparsers.add_parser("shell", help="Start interactive shell")

    memory_parser = subparsers.add_parser("memory", help="Manage memories")
    memory_sub = memory_parser.add_subparsers(dest="memory_action")
    memory_sub.add_parser("list", help="List recent memories")
    search_parser = memory_sub.add_parser("search", help="Search memories")
    search_parser.add_argument("query", help="Search query")
    memory_sub.add_parser("stats", help="Show memory statistics")
    clear_parser = memory_sub.add_parser("clear", help="Clear memories")
    clear_parser.add_argument("--confirm", action="store_true", help="Skip confirmation")

    subparsers.add_parser("stats", help="Show system statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\nTip: Run 'jarvis shell' for interactive mode")
        sys.exit(0)

    client = JarvisClient()

    try:
        if args.command == "chat":
            message = " ".join(args.message) if args.message else ""
            if not message:
                display_error("Please provide a message")
                sys.exit(1)
            print(f"\n[You]: {message}\n")
            print("[JARVIS]: ", end="", flush=True)
            response = client.chat(message)
            print(response)
            print()

        elif args.command == "shell":
            simple_shell(client)

        elif args.command == "memory":
            if not args.memory_action:
                display_error("Specify an action: list, search, stats, clear")
                sys.exit(1)

            if args.memory_action == "list":
                memories = client.get_memories()
                display_memory(memories)

            elif args.memory_action == "search":
                results = client.search_memory(args.query)
                display_memory(results, title=f"Search: {args.query}")

            elif args.memory_action == "stats":
                stats = client.get_memory_stats()
                print(json.dumps(stats, indent=2))

            elif args.memory_action == "clear":
                if not args.confirm:
                    confirm = input("Clear all memories? (y/N): ")
                    if confirm.lower() != "y":
                        print("Cancelled")
                        sys.exit(0)
                result = client.clear_memories()
                print(f"Cleared {result.get('deleted', 0)} memories")

        elif args.command == "stats":
            stats = client.get_stats()
            display_stats(stats)

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        display_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
