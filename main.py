"""
JARVIS - Just A Rather Very Intelligent System
Main entry point for the JARVIS AI Assistant.
"""

import sys
import signal
import argparse
import threading
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
from brain.router import CommandRouter
from brain.tools import create_default_registry

# Import memory
from memory import MemoryManager

# Import backend
from backend.main import create_app


# ASCII Banner
BANNER = """
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
=============================================
   Starting up...
"""

# Global references for shutdown
app_config = None
memory_manager = None
agent = None
voice_pipeline = None
router = None


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    log_level = "DEBUG" if verbose else "INFO"
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )
    
    # Add file handler
    logger.add(
        "./data/jarvis.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )


def start_ui_server(config):
    """Start the FastAPI backend server in a thread."""
    import uvicorn
    
    app = create_app()
    
    config_dict = {
        "host": config.ui_host,
        "port": config.ui_port,
        "app": app,
        "log_level": "info",
    }
    
    uvicorn.run(**config_dict)


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
    setup_logging(args.verbose)
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
    logger.info(f"Whisper Model: {config.whisper_model}")
    logger.info(f"LLM Model: {config.ollama_model}")
    
    app_config = config
    
    # 3. Initialize memory
    logger.info("Initializing memory...")
    memory_manager = MemoryManager(config)
    logger.info("Memory initialized")
    
    # 4. Initialize agent
    logger.info("Initializing agent...")
    agent = ReActAgent()
    logger.info("Agent ready")
    
    # 4b. Initialize command router
    if not args.disable_router:
        logger.info("Initializing command router...")
        tool_registry = create_default_registry()
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
                stt_model=config.whisper_model,
                stt_device="cpu"
            )
            logger.info("Voice pipeline ready")
        except Exception as e:
            logger.warning(f"Voice pipeline failed to initialize: {e}")
            logger.warning("Running in text-only mode")
            args.text_only = True
    
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
                
                if router:
                    # Use smart routing
                    route_result = router.route(user_input)
                    
                    if route_result.route_type.value == "direct_tool":
                        # Execute directly without LLM
                        logger.info(f"Direct tool execution: {route_result.tool_name}")
                        response = router.execute_direct(route_result)
                    elif route_result.route_type.value == "llm_agent":
                        # Explicitly requested LLM
                        response = agent.run(user_input)
                    else:
                        # Unknown - default to LLM (safer)
                        logger.info("Unknown command, routing to LLM")
                        response = agent.run(user_input)
                else:
                    # Router disabled, use LLM
                    response = agent.run(user_input)
                
                print(f"\nJARVIS: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                print(f"\nError: {e}")
        
        logger.info("Exiting text-only mode")


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
