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
  %(prog)s                                    # Use whitelisted_tools.txt, 5s delay
  %(prog)s --delay 3                          # 3 second delay
  %(prog)s --debug                            # Enable debug output
  %(prog)s --tools "Read file,Edit file"      # Override tools (ignore file)
  %(prog)s --tools-file my_tools.txt          # Use custom tools file
  %(prog)s --delay 10 --debug --tools-file custom.txt  # Combine options
        """
    )
    
    parser.add_argument(
        "--delay", "-d", 
        type=float, 
        default=5.0,
        help="Response delay in seconds (default: 5.0)"
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
    
    args = parser.parse_args()

    print("Claude Code Auto Responder")
    print("==========================")
    print()
    print("This tool will automatically select:")
    print("• 'Yes, and don't ask again' when available")
    print("• 'Yes' otherwise")
    print()

    # Create configuration
    if args.tools:
        # Command line tools override everything
        tools = [tool.strip() for tool in args.tools.split(',')]
        config = Config(whitelisted_tools=tools, default_timeout=args.delay)
        print(f"Using command line tools: {', '.join(tools)}")
    else:
        # Load from tools file
        tools = Config.load_whitelisted_tools(args.tools_file)
        config = Config(whitelisted_tools=tools, default_timeout=args.delay)
        if args.tools_file != "whitelisted_tools.txt":
            print(f"Using tools from {args.tools_file}: {len(tools)} tools loaded")

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("⚠️  This tool currently only supports macOS")
        sys.exit(1)

    # Create and start auto responder
    responder = AutoResponder(config, debug=args.debug)
    responder.start_monitoring()


if __name__ == "__main__":
    main()