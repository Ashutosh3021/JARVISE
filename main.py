"""
JARVIS - Just A Rather Very Intelligent System
Main entry point for the JARVIS AI Assistant.
"""

import sys
import signal
import argparse
import threading
import time
import socket
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

# Import core modules
from core.logger import setup_logging
from core.hardware import detect_hardware
from core.config import load_config

# Import brain
from brain.agent import ReActAgent
from brain.router import CommandRouter, RouteType
from brain.tools import create_tools_registry

# Import memory
from memory import MemoryManager

# Import backend
from backend.main import create_app


# ASCII Banner
BANNER = r"""
     ██  █████  ██████  ██    ██ ██ ███████ 
     ██ ██   ██ ██   ██ ██    ██ ██ ██      
     ██ ███████ ██████  ██    ██ ██ ███████ 
██   ██ ██   ██ ██   ██  ██  ██  ██      ██ 
 █████  ██   ██ ██   ██   ████   ██ ███████
============================================
   Starting up...
"""

# Global references for shutdown
app_config = None
memory_manager = None
agent = None
voice_pipeline = None
router = None


def start_ui_server(config):
    """Start the FastAPI backend server in a thread."""
    import uvicorn
    import socket
    
    app = create_app()
    
    # Find an available port starting from ui_port
    port = config.ui_port
    max_attempts = 10
    
    while max_attempts > 0:
        if _is_port_available(config.ui_host, port):
            break
        port += 1
        max_attempts -= 1
    
    if max_attempts == 0:
        logger.warning(f"Could not find available port near {config.ui_port}, using default 8000")
        port = 8000
    
    config_dict = {
        "host": config.ui_host,
        "port": port,
        "app": app,
        "log_level": "info",
    }
    
    try:
        uvicorn.run(**config_dict)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is in use. Please free the port or run with a different port.")
        else:
            logger.error(f"UI server error: {e}")


def _is_port_available(host: str, port: int) -> bool:
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        sock.close()
        return False  # Port is in use
    except (socket.timeout, ConnectionRefusedError, OSError):
        return True  # Port is available


def signal_handler(sig, frame):
    """Handle graceful shutdown on Ctrl+C."""
    logger.info("Shutting down JARVIS...")
    
    # Stop voice pipeline if running
    global voice_pipeline
    if voice_pipeline:
        try:
            voice_pipeline.stop()
            logger.info("Voice pipeline stopped")
        except Exception as e:
            logger.error(f"Error stopping voice pipeline: {e}")
    
    logger.info("JARVIS shutdown complete")
    sys.exit(0)


def exception_handler(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc_type.__name__}: {exc_value}")
    import traceback
    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


ORANGE = "\033[38;5;208m"
RESET = "\033[0m"


def run_jarvis(args):
    """Main JARVIS run loop."""
    global app_config, memory_manager, agent, voice_pipeline, router
    
    # Print banner
    print(BANNER)
    print("=" * 50)
    print("JARVIS AI Assistant - Starting...")
    print("=" * 50)
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(verbose=args.verbose)
    logger.info("Logger initialized")
    
    # 1. Hardware detection
    logger.info("Detecting hardware...")
    hw = detect_hardware()
    logger.info(f"Hardware: {hw.cpu_physical_cores} physical cores, {hw.cpu_logical_cores} logical cores")
    logger.info(f"GPU: {hw.gpu_name}, VRAM: {hw.vram_total_mb}MB")
    logger.info(f"Has NVIDIA: {hw.has_nvidia}, Has AMD: {hw.has_amd}")
    
    # 2. Load configuration (auto-selects models based on hardware)
    logger.info("Loading configuration...")
    config = load_config(hw.vram_total_mb)
    logger.info(f"Profile: {config.profile.value}")
    logger.info(f"STT Model: {config.stt_model}")
    logger.info(f"LLM Model: {config.ollama_model}")
    
    app_config = config
    
    # 3. Initialize memory
    logger.info("Initializing memory...")
    memory_manager = MemoryManager(config)
    logger.info("Memory initialized")
    
    # 4. Initialize agent
    logger.info("Initializing agent...")
    tool_registry = create_tools_registry()
    agent = ReActAgent(tool_registry=tool_registry)
    logger.info("Agent ready")
    
    # 4b. Initialize command router
    if not args.disable_router:
        logger.info("Initializing command router...")
        router = CommandRouter(tool_registry=tool_registry)
        logger.info("Command router ready")
        
        # Register router with API for stats
        try:
            from backend.api.routes.stats import set_router
            set_router(router)
            logger.info("Router stats registered with API")
        except Exception as e:
            logger.warning(f"Could not register router stats: {e}")
        
        # Register router and registry with learning API
        try:
            from backend.api.routes.learn import set_tool_registry, set_command_router
            set_tool_registry(tool_registry)
            set_command_router(router)
            logger.info("Learning API registered")
        except Exception as e:
            logger.warning(f"Could not register learning API: {e}")
    else:
        router = None
        logger.info("Command router disabled")
    
    # 5. Initialize voice (if not text-only mode)
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
            logger.warning(f"Voice pipeline failed to initialize: {e}")
            logger.warning("Running in text-only mode")
            args.text_only = True
        else:
            # Wire transcription callback — Contract C-7: MUST be before start()
            def handle_transcription(text: str, confidence: float):
                """Process transcribed speech through router or agent, then speak response."""
                logger.info(f"{ORANGE}User: '{text}'{RESET} (confidence: {confidence:.2f})")
                try:
                    # Get memory context BEFORE agent.run() - per requirement memory loaded before streaming
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
                    
                    # Auto-save every exchange to memory after response
                    if memory_manager:
                        memory_manager.save_conversation(text, response)
                    
                    voice_pipeline.speak_async(response)
                except Exception as e:
                    logger.error(f"Error processing voice input: {e}")
                    voice_pipeline.speak_async(f"I encountered an error processing that.")
            
            voice_pipeline.on_transcription(handle_transcription)
            voice_pipeline.start()
            logger.info("Voice pipeline started")
    
    # 6. Start UI server (if not headless) in background thread
    if not args.headless:
        logger.info(f"Starting UI server at http://{config.ui_host}:{config.ui_port}")
        try:
            server_thread = threading.Thread(target=start_ui_server, args=(config,), daemon=True)
            server_thread.start()
            logger.info("UI server started in background")
        except Exception as e:
            logger.error(f"UI server failed: {e}")
            logger.info("Continuing without UI...")
    
    # Main loop for text-only mode
    if args.text_only:
        logger.info("Running in text-only mode")
        logger.info("Type your commands below (or 'exit' to quit)")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'exit()']:
                    break
                
                if not user_input:
                    continue
                
                # Process through router or agent
                logger.info(f"Processing: {user_input}")
                
                # Get memory context BEFORE agent.run() - per requirement memory loaded before streaming
                memory_context = memory_manager.format_context_for_prompt(user_input) if memory_manager else None
                
                logger.info(f"{ORANGE}User: {user_input}{RESET}")
                
                if router:
                    # Use smart routing
                    route_result = router.route(user_input)
                    
                    if route_result.route_type == RouteType.DIRECT_TOOL:
                        # Execute directly without LLM
                        logger.info(f"Direct tool execution: {route_result.tool_name}")
                        response = router.execute_direct(route_result)
                    elif route_result.route_type == RouteType.LLM_AGENT:
                        # Explicitly requested LLM
                        response = agent.run(user_input, memory_context=memory_context)
                    else:
                        # Unknown - default to LLM (safer)
                        logger.info("Unknown command, routing to LLM")
                        response = agent.run(user_input, memory_context=memory_context)
                        router._stats.llm_agent_calls += 1
                else:
                    # Router disabled, use LLM
                    response = agent.run(user_input, memory_context=memory_context)
                
                logger.info(f"{ORANGE}JARVIS: {response}{RESET}")
                
                # Auto-save every exchange to memory after response
                if memory_manager:
                    memory_manager.save_conversation(user_input, response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                print(f"\nError: {e}")
        
        logger.info("Exiting text-only mode")
    
    else:
        # Voice mode - keep the program running
        logger.info("JARVIS is ready! (Voice mode)")
        logger.info("Press Ctrl+C to exit")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="JARVIS AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Run without voice (text input only)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without UI (backend only)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--disable-router",
        action="store_true",
        help="Disable command router (always use LLM)"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    sys.excepthook = exception_handler
    
    # Create data directory if needed
    Path("./data").mkdir(exist_ok=True)
    
    # Run JARVIS
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
