"""
JARVIS Interactive Shell
"""

import asyncio
import sys

from cli.client import JarvisClient


class JarvisShell:
    """Interactive shell for JARVIS"""
    
    def __init__(self, client: JarvisClient):
        self.client = client
        
    def run(self):
        """Run the interactive shell"""
        simple_shell(self.client)


# Keep simple version as default
def simple_shell(client: JarvisClient):
    """Simple shell using input() - cross-platform compatible"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                    JARVIS Interactive Shell               ║
║                                                           ║
║  Commands:                                                ║
║    :help     - Show this help                            ║
║    :memory   - View memories                              ║
║    :stats    - Show system stats                          ║
║    :clear    - Clear conversation                        ║
║    :quit     - Exit shell                                ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Check server
    if not asyncio.run(client.health_check()):
        print("✗ Cannot connect to JARVIS server")
        print("  Start server with: python main.py")
        return
    
    print("✓ Connected to JARVIS\n")
    
    messages = []
    
    while True:
        try:
            user_input = input("\n[You] ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
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
                    result = asyncio.run(client.get_memories(limit=10))
                    memories = result.get("memories", [])
                    
                    if not memories:
                        print("No memories found")
                    else:
                        print(f"\n--- Recent Memories ({len(memories)}) ---")
                        for i, mem in enumerate(memories, 1):
                            query = mem.get("query", "")[:60]
                            print(f"{i}. {query}")
                            
                elif cmd == "stats":
                    print("\nFetching system stats...")
                    result = asyncio.run(client.get_stats())
                    
                    cpu = result.get("cpu", {}).get("percent", "N/A")
                    mem = result.get("memory", {})
                    mem_used = mem.get("used_gb", "N/A")
                    mem_total = mem.get("total_gb", "N/A")
                    mem_pct = mem.get("percent", "N/A")
                    
                    print(f"""
System Statistics:
  CPU:     {cpu}%
  Memory:  {mem_used:.1f}GB / {mem_total:.1f}GB ({mem_pct}%)
                    """)
                    
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
            
            # Send to JARVIS
            print("\n[JARVIS] ", end="", flush=True)
            response = asyncio.run(client.chat(user_input))
            print(response)
            
            # Store in history
            messages.append(("user", user_input))
            messages.append(("assistant", response))
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    client = JarvisClient()
    simple_shell(client)
