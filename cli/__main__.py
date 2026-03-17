"""
JARVIS CLI - Command-line interface for JARVIS AI Assistant

Install:
    pip install -e .

Usage:
    jarvis chat "Hello, how are you?"
    jarvis shell           # Interactive mode
    jarvis memory list     # View memories
    jarvis memory search "python"
    jarvis stats           # System stats
    jarvis settings show  # Show settings
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.client import JarvisClient
from cli.shell import JarvisShell
from cli.display import display_chat, display_memory, display_stats, display_error


def main():
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS AI Assistant - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jarvis chat "Hello, how are you?"
  jarvis shell                  # Start interactive shell
  jarvis memory list            # List memories
  jarvis memory search "query"  # Search memories
  jarvis stats                  # Show system stats
  jarvis settings show          # Show settings
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send a message to JARVIS")
    chat_parser.add_argument("message", nargs="*", help="Message to send")
    chat_parser.add_argument("--stream", action="store_true", help="Stream response")
    
    # Shell command
    subparsers.add_parser("shell", help="Start interactive shell mode")
    
    # Memory command
    memory_parser = subparsers.add_parser("memory", help="Manage memories")
    memory_sub = memory_parser.add_subparsers(dest="memory_action")
    
    # Memory list
    memory_sub.add_parser("list", help="List all memories")
    
    # Memory search
    search_parser = memory_sub.add_parser("search", help="Search memories")
    search_parser.add_argument("query", help="Search query")
    
    # Memory stats
    memory_sub.add_parser("stats", help="Show memory statistics")
    
    # Memory clear
    clear_parser = memory_sub.add_parser("clear", help="Clear memories")
    clear_parser.add_argument("--confirm", action="store_true", help="Skip confirmation")
    
    # Stats command
    subparsers.add_parser("stats", help="Show system statistics")
    
    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Manage settings")
    settings_sub = settings_parser.add_subparsers(dest="settings_action")
    
    settings_sub.add_parser("show", help="Show current settings")
    
    # Voice command
    voice_parser = subparsers.add_parser("voice", help="Voice interaction")
    voice_parser.add_argument("--listen", action="store_true", help="Listen for voice input")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Server management")
    server_sub = server_parser.add_subparsers(dest="server_action")
    server_sub.add_parser("start", help="Start JARVIS server")
    server_sub.add_parser("stop", help="Stop JARVIS server")
    server_sub.add_parser("status", help="Check server status")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to shell if no command
    if not args.command:
        parser.print_help()
        print("\nTip: Run 'jarvis shell' for interactive mode")
        sys.exit(0)
    
    # Create client
    client = JarvisClient()
    
    # Execute command
    try:
        if args.command == "chat":
            message = " ".join(args.message) if args.message else ""
            if not message:
                display_error("Please provide a message")
                sys.exit(1)
            asyncio.run(chat_command(client, message, args.stream))
            
        elif args.command == "shell":
            shell = JarvisShell(client)
            shell.run()
            
        elif args.command == "memory":
            asyncio.run(memory_command(client, args))
            
        elif args.command == "stats":
            asyncio.run(stats_command(client))
            
        elif args.command == "settings":
            asyncio.run(settings_command(client, args))
            
        elif args.command == "voice":
            asyncio.run(voice_command(client, args))
            
        elif args.command == "server":
            server_command(args)
            
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        display_error(f"Error: {e}")
        sys.exit(1)


async def chat_command(client: JarvisClient, message: str, stream: bool = False):
    """Handle chat command"""
    print(f"\n[You]: {message}\n")
    print("[JARVIS]: ", end="", flush=True)
    
    response = await client.chat(message, stream=stream)
    
    if stream:
        print(response)
    else:
        print(response)
    print()


async def memory_command(client: JarvisClient, args):
    """Handle memory command"""
    if not args.memory_action:
        display_error("Please specify a memory action (list, search, stats, clear)")
        sys.exit(1)
    
    if args.memory_action == "list":
        memories = await client.get_memories()
        display_memory(memories)
        
    elif args.memory_action == "search":
        results = await client.search_memory(args.query)
        display_memory(results, title=f"Search results for: {args.query}")
        
    elif args.memory_action == "stats":
        stats = await client.get_memory_stats()
        print(json.dumps(stats, indent=2))
        
    elif args.memory_action == "clear":
        if not args.confirm:
            confirm = input("Are you sure you want to clear all memories? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                sys.exit(0)
        result = await client.clear_memories()
        print(f"Cleared {result.get('deleted', 0)} memories")


async def stats_command(client: JarvisClient):
    """Handle stats command"""
    stats = await client.get_stats()
    display_stats(stats)


async def settings_command(client: JarvisClient, args):
    """Handle settings command"""
    if args.settings_action == "show":
        settings = await client.get_settings()
        print(json.dumps(settings, indent=2))
    else:
        display_error("Please specify a settings action (show)")


async def voice_command(client: JarvisClient, args):
    """Handle voice command"""
    if args.listen:
        print("Voice input not yet implemented in CLI")
        print("Use 'jarvis chat' for text-based interaction")
    else:
        print("Voice mode requires server to be running with voice pipeline")
        print("Use: jarvis server start")


def server_command(args):
    """Handle server command"""
    if not args.server_action:
        display_error("Please specify a server action (start, stop, status)")
        sys.exit(1)
    
    if args.server_action == "start":
        print("Starting JARVIS server...")
        print("Run 'python main.py' in the JARVIS directory")
        
    elif args.server_action == "stop":
        print("Stopping JARVIS server...")
        # Would implement graceful shutdown
        
    elif args.server_action == "status":
        import requests
        try:
            r = requests.get("http://localhost:8000/health", timeout=2)
            if r.status_code == 200:
                print("JARVIS server is running at http://localhost:8000")
            else:
                print("Server returned unexpected status")
        except:
            print("JARVIS server is not running")


if __name__ == "__main__":
    main()
