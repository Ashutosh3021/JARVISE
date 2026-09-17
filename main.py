"""
JARVIS - Just A Rather Very Intelligent System
Pure CLI entry point. No server, no UI.
"""

import sys
import os
import signal
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

from core.logger import setup_logging
from core.hardware import detect_hardware
from core.config import load_config
from brain.agent import ReActAgent
from brain.router import CommandRouter, RouteType
from brain.tools import create_tools_registry
from brain.providers import OllamaProvider, create_cloud_provider
from memory import MemoryManager


BANNER = r"""
     ██  █████  ██████  ██    ██ ██ ███████ 
     ██ ██   ██ ██   ██ ██    ██ ██ ██      
     ██ ███████ ██████  ██    ██ ██ ███████ 
 ██   ██ ██   ██ ██   ██  ██  ██  ██      ██ 
  █████  ██   ██ ██   ██   ████   ██ ███████
============================================
"""

ORANGE = "\033[38;5;208m"
RESET = "\033[0m"

PROVIDER_CHOICES = ["groq", "openrouter", "google"]


def signal_handler(sig, frame):
    logger.info("Shutting down JARVIS...")
    sys.exit(0)


def prompt_way():
    """Interactive provider selection flow."""
    print(f"\n{ORANGE}Select LLM Provider:{RESET}")
    for i, name in enumerate(PROVIDER_CHOICES, 1):
        print(f"  {i}. {name}")
    print()

    while True:
        choice = input("Enter number (1-3): ").strip()
        if choice in ("1", "2", "3"):
            break
        print("Invalid choice, try again.")

    provider = PROVIDER_CHOICES[int(choice) - 1]
    print(f"\nSelected: {ORANGE}{provider}{RESET}")

    # Get API key
    env_key_map = {
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "google": "GOOGLE_AI_API_KEY",
    }
    env_model_map = {
        "groq": "GROQ_MODEL",
        "openrouter": "OPENROUTER_MODEL",
        "google": "GOOGLE_AI_MODEL",
    }

    env_key = env_key_map[provider]
    saved_key = os.environ.get(env_key, "")

    if saved_key:
        print(f"Found saved API key for {provider} (****{saved_key[-4:]})")
        use_saved = input("Use saved key? [Y/n]: ").strip().lower()
        if use_saved in ("", "y", "yes"):
            api_key = saved_key
        else:
            api_key = input(f"Enter {provider} API key: ").strip()
    else:
        api_key = input(f"Enter {provider} API key: ").strip()

    if not api_key:
        print("No API key provided, aborting.")
        return None, None, None

    # Get model name
    default_model = os.environ.get(env_model_map[provider], "")
    if default_model:
        print(f"Default model: {default_model}")
        use_default = input("Use default? [Y/n]: ").strip().lower()
        if use_default in ("", "y", "yes"):
            model = default_model
        else:
            model = input("Enter exact model name: ").strip()
    else:
        model = input("Enter exact model name: ").strip()

    if not model:
        print("No model name provided, aborting.")
        return None, None, None

    # Save to .env for next time
    _save_to_env(env_key, api_key)
    _save_to_env(env_model_map[provider], model)

    return provider, api_key, model


def _save_to_env(key: str, value: str):
    """Save a key-value pair to .env file."""
    env_path = Path(".env")
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")


def resolve_provider(args, config):
    """
    Resolve which LLM provider to use based on CLI args.
    
    Returns: (provider_instance, model_name)
    """
    # --way: interactive cloud provider selection
    if args.way:
        provider_name, api_key, model = prompt_way()
        if provider_name is None:
            sys.exit(1)
        llm = create_cloud_provider(provider_name, api_key, model)
        return llm, model

    # Check if a model name was given as positional (e.g., --mistral)
    model_name = getattr(args, "model_name", None)

    if model_name:
        # --<model> -run: pull if needed, then run with that model
        host = config.ollama_host
        ollama = OllamaProvider(host=host, model=model_name)

        if args.run:
            # Check if model is pulled
            models = ollama.list_models()
            pulled_names = {m["name"] for m in models}
            if model_name not in pulled_names:
                # Try partial match
                found = any(model_name in n for n in pulled_names)
                if not found:
                    print(f"Model '{model_name}' not found locally. Pulling...")
                    if not ollama.pull_model(model_name):
                        print(f"Failed to pull {model_name}")
                        sys.exit(1)

        return ollama, model_name

    # --model or no flag: auto-detect best local model
    host = config.ollama_host
    ollama = OllamaProvider(host=host, model=config.ollama_model)

    if args.model:
        best = ollama.get_best_model(config.vram_mb)
        print(f"Best local model: {ORANGE}{best}{RESET}")
        ollama._model = best
        return ollama, best

    # Default: use config model
    return ollama, config.ollama_model


def run_jarvis(args):
    global voice_pipeline

    print(BANNER)

    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(verbose=args.verbose)
    logger.info("Logger initialized")

    logger.info("Detecting hardware...")
    hw = detect_hardware()
    logger.info(f"Hardware: {hw.cpu_physical_cores} physical cores, {hw.cpu_logical_cores} logical cores")
    logger.info(f"GPU: {hw.gpu_name}, VRAM: {hw.vram_total_mb}MB")

    logger.info("Loading configuration...")
    config = load_config(hw.vram_total_mb)
    logger.info(f"Profile: {config.profile.value}")
    logger.info(f"STT Model: {config.stt_model}")

    logger.info("Resolving LLM provider...")
    llm_provider, model_name = resolve_provider(args, config)
    logger.info(f"Provider: {llm_provider.provider_name}, Model: {model_name}")

    logger.info("Initializing memory...")
    memory_manager = MemoryManager(config)
    logger.info("Memory initialized")

    logger.info("Initializing agent...")
    tool_registry = create_tools_registry()
    agent = ReActAgent(llm_client=llm_provider, tool_registry=tool_registry)
    logger.info("Agent ready")

    router = None
    if not args.disable_router:
        logger.info("Initializing command router...")
        router = CommandRouter(tool_registry=tool_registry)
        logger.info("Command router ready")

    voice_pipeline = None
    if not args.text_only:
        logger.info("Initializing voice pipeline...")
        try:
            from voice.pipeline import VoicePipeline
            voice_pipeline = VoicePipeline(
                stt_model=config.stt_model,
                stt_device="cpu"
            )
            logger.info("Voice pipeline ready")
        except Exception as e:
            logger.warning(f"Voice pipeline failed: {e}")
            logger.warning("Running in text-only mode")
            args.text_only = True
        else:
            def handle_transcription(text: str, confidence: float):
                logger.info(f"{ORANGE}User: '{text}'{RESET} (confidence: {confidence:.2f})")
                try:
                    memory_context = memory_manager.format_context_for_prompt(text) if memory_manager else None

                    if router:
                        route_result = router.route(text)
                        if route_result.route_type == RouteType.DIRECT_TOOL:
                            response = router.execute_direct(route_result)
                        elif route_result.route_type == RouteType.CHAIN:
                            response = router.execute_chain(route_result, text)
                        else:
                            response = agent.run(text, memory_context=memory_context)
                    else:
                        response = agent.run(text, memory_context=memory_context)

                    logger.info(f"{ORANGE}JARVIS: {response}{RESET}")

                    if memory_manager:
                        memory_manager.save_conversation(text, response)

                    voice_pipeline.speak_async(response)
                except Exception as e:
                    logger.error(f"Error processing voice input: {e}")
                    voice_pipeline.speak_async("I encountered an error processing that.")

            voice_pipeline.on_transcription(handle_transcription)
            voice_pipeline.start()
            logger.info("Voice pipeline started")

    logger.info("JARVIS ready. Type your commands below (or 'exit' to quit)")
    if voice_pipeline:
        logger.info("Voice mode active — press space to speak")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit', 'exit()']:
                break
            if not user_input:
                continue

            memory_context = memory_manager.format_context_for_prompt(user_input) if memory_manager else None
            logger.info(f"{ORANGE}User: {user_input}{RESET}")

            if router:
                route_result = router.route(user_input)
                if route_result.route_type == RouteType.DIRECT_TOOL:
                    logger.info(f"Direct tool execution: {route_result.tool_name}")
                    response = router.execute_direct(route_result)
                elif route_result.route_type == RouteType.CHAIN:
                    response = router.execute_chain(route_result, user_input)
                else:
                    response = agent.run(user_input, memory_context=memory_context)
            else:
                response = agent.run(user_input, memory_context=memory_context)

            logger.info(f"{ORANGE}JARVIS: {response}{RESET}")

            if memory_manager:
                memory_manager.save_conversation(user_input, response)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            print(f"\nError: {e}")

    logger.info("JARVIS shutdown complete")


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS AI Assistant — Pure CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jarvise                      Run with auto-detected best local model
  jarvise --model              Show best model for your hardware
  jarvise --llama3.2 -run      Pull llama3.2 if needed, then run
  jarvise --qwen2.5-coder:7b  Run with specific Ollama model
  jarvise --way                Select cloud provider (Groq/OpenRouter/Google)
  jarvise --text-only          Text-only mode (no voice)
        """,
    )
    parser.add_argument("--text-only", action="store_true", help="Run without voice (text input only)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--disable-router", action="store_true", help="Disable command router (always use LLM)")
    parser.add_argument("--model", action="store_true", help="Auto-detect and show best local model")
    parser.add_argument("--way", action="store_true", help="Interactive cloud provider selection")
    parser.add_argument("--run", action="store_true", help="Pull model if needed, then run")
    # Dynamic model name: any arg starting with -- that isn't recognized
    # We use parse_known_args to capture unknown args as model names
    args, unknown = parser.parse_known_args()

    # Treat unknown args as model name (e.g., --mistral, --llama3.2)
    model_name = None
    for u in unknown:
        if u.startswith("--"):
            model_name = u[2:]  # strip --
            break
        elif not u.startswith("-"):
            model_name = u
            break

    if model_name:
        args.model_name = model_name
    else:
        args.model_name = None

    signal.signal(signal.SIGINT, signal_handler)
    Path("./data").mkdir(exist_ok=True)

    try:
        run_jarvis(args)
    except KeyboardInterrupt:
        logger.info("JARVIS interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
