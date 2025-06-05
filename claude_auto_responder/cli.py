"""Command-line interface for Claude Auto Responder"""

import argparse
import sys

from .config.settings import Config
from .core.responder import AutoResponder


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Claude Auto Responder - Automatically respond to Claude Code prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Monitor all windows, 0s delay
  %(prog)s --single                           # Monitor only focused window
  %(prog)s --delay 3                          # 3 second delay before responding
  %(prog)s --debug                            # Enable debug output
  %(prog)s --tools "Read file,Edit file"      # Override tools (ignore file)
  %(prog)s --tools-file my_tools.txt          # Use custom tools file
  %(prog)s --single --delay 5 --debug         # Combine options
        """
    )
    
    parser.add_argument(
        "--delay", "-d", 
        type=float, 
        default=0.0,
        help="Response delay in seconds (default: 0.0)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode for troubleshooting"
    )
    
    parser.add_argument(
        "--tools", "-t",
        type=str,
        help="Comma-separated list of whitelisted tools (overrides tools file)"
    )
    
    parser.add_argument(
        "--tools-file", "-f",
        type=str,
        default="whitelisted_tools.txt",
        help="Path to whitelisted tools file (default: whitelisted_tools.txt)"
    )
    
    parser.add_argument(
        "--single", "-s",
        action="store_true",
        help="Monitor only the focused terminal window (default: monitor all windows)"
    )
    
    parser.add_argument(
        "--enable-sleep-detection",
        action="store_true",
        help="Enable automatic pause/resume on system sleep/wake (experimental)"
    )
    
    args = parser.parse_args()

    print("Claude Code Auto Responder")
    print("==========================")
    print()
    print("This tool will automatically select:")
    print("• 'Yes, and don't ask again' when available")
    print("• 'Yes' otherwise")
    print()

    # Create configuration
    enable_sleep_detection = args.enable_sleep_detection
    
    if args.tools:
        # Command line tools override everything
        tools = [tool.strip() for tool in args.tools.split(',')]
        config = Config(
            whitelisted_tools=tools, 
            default_timeout=args.delay,
            enable_sleep_detection=enable_sleep_detection
        )
        print(f"Using command line tools: {', '.join(tools)}")
    else:
        # Load from tools file
        tools = Config.load_whitelisted_tools(args.tools_file)
        config = Config(
            whitelisted_tools=tools, 
            default_timeout=args.delay,
            enable_sleep_detection=enable_sleep_detection
        )
        if args.tools_file != "whitelisted_tools.txt":
            print(f"Using tools from {args.tools_file}: {len(tools)} tools loaded")

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("⚠️  This tool currently only supports macOS")
        sys.exit(1)

    # Create and start auto responder
    # Default is to monitor all windows (opposite of --single flag)
    responder = AutoResponder(config, debug=args.debug, monitor_all=not args.single)
    responder.start_monitoring()


if __name__ == "__main__":
    main()