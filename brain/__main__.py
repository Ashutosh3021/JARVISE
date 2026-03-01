"""
JARVIS Brain Module - CLI Entry Point

Provides command-line interface for testing the brain layer.
"""

import argparse
import sys

from loguru import logger

from brain.client import OllamaClient
from brain.agent import ReActAgent
from brain.tools import create_default_registry
from brain import PromptBuilder


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=level, format="<level>{level}: {message}</level>")


def health_check(args: argparse.Namespace) -> int:
    """Run health check on Ollama server."""
    client = OllamaClient()
    
    logger.info("Checking Ollama server health...")
    
    if client.health_check(retries=args.retries):
        logger.info("Ollama server is healthy!")
        
        models = client.list_models()
        if models:
            logger.info("Available models:")
            for model in models:
                logger.info(f"  - {model['name']} ({model['size'] // (1024**3)} GB)")
        else:
            logger.warning("No models found")
        
        return 0
    else:
        logger.error("Ollama server is not responding")
        return 1


def chat(args: argparse.Namespace) -> int:
    """Run interactive chat with the agent."""
    client = OllamaClient()
    
    if not client.health_check():
        logger.error("Ollama server is not running. Start it with 'ollama serve'")
        return 1
    
    registry = create_default_registry()
    agent = ReActAgent(llm_client=client, tool_registry=registry)
    
    logger.info("Starting chat session. Type 'quit' or 'exit' to end.")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ("quit", "exit", "q"):
                logger.info("Ending chat session")
                break
            
            if not user_input:
                continue
            
            print("\nJARVIS: ", end="", flush=True)
            response = agent.run(user_input)
            print(response)
            
        except KeyboardInterrupt:
            logger.info("\nInterrupted")
            break
        except EOFError:
            break
    
    return 0


def simple_chat(args: argparse.Namespace) -> int:
    """Run a single chat message."""
    client = OllamaClient()
    
    if not client.health_check():
        logger.error("Ollama server is not running")
        return 1
    
    pb = PromptBuilder()
    messages = pb.build_simple(args.text)
    
    response = client.chat(messages)
    content = response.get("message", {}).get("content", "")
    
    print(content)
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JARVIS Brain Layer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    health_parser = subparsers.add_parser("health", help="Check Ollama server health")
    health_parser.add_argument(
        "-r", "--retries",
        type=int,
        default=3,
        help="Number of retry attempts (default: 3)"
    )
    
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat session")
    
    subparsers.add_parser("models", help="List available Ollama models")
    
    simple_parser = subparsers.add_parser("say", help="Send a single message and print response")
    simple_parser.add_argument("text", help="Text to send to the agent")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if args.command == "health":
        return health_check(args)
    elif args.command == "chat":
        return chat(args)
    elif args.command == "models":
        client = OllamaClient()
        models = client.list_models()
        for model in models:
            print(f"{model['name']}: {model['size'] // (1024**3)} GB")
        return 0
    elif args.command == "say":
        return simple_chat(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
