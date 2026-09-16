"""
JARVIS - Just A Rather Very Intelligent System
Pure CLI entry point. No server, no UI.
"""

import sys
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


def signal_handler(sig, frame):
    logger.info("Shutting down JARVIS...")
    sys.exit(0)


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
    logger.info(f"LLM Model: {config.ollama_model}")

    logger.info("Initializing memory...")
    memory_manager = MemoryManager(config)
    logger.info("Memory initialized")

    logger.info("Initializing agent...")
    tool_registry = create_tools_registry()
    agent = ReActAgent(tool_registry=tool_registry)
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
    )
    parser.add_argument("--text-only", action="store_true", help="Run without voice (text input only)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--disable-router", action="store_true", help="Disable command router (always use LLM)")
    args = parser.parse_args()

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
