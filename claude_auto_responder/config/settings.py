"""Configuration management for Claude Auto Responder"""

from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    """Configuration settings"""
    whitelisted_tools: List[str]
    default_timeout: float
    check_interval: float = 1.0
    enable_sleep_detection: bool = False

    @classmethod
    def load_whitelisted_tools(cls, tools_file: str = "whitelisted_tools.txt") -> List[str]:
        """Load whitelisted tools from a text file"""
        try:
            with open(tools_file, 'r') as f:
                tools = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        tools.append(line)
                return tools
        except FileNotFoundError:
            print(f"⚠️  Tools file '{tools_file}' not found, using defaults")
            return cls._get_default_tools()
        except Exception as e:
            print(f"⚠️  Error reading tools file: {e}")
            return cls._get_default_tools()
    
    @classmethod
    def _get_default_tools(cls) -> List[str]:
        """Get default whitelisted tools"""
        return [
            "Read file", "Read files", "Edit file", "Edit files",
            "Bash command", "Bash", "Write", "Write file", "Write files",
            "MultiEdit", "Grep", "Glob", "LS", "WebFetch", "WebSearch"
        ]

    @classmethod
    def get_default(cls) -> "Config":
        """Get default configuration"""
        return cls(
            whitelisted_tools=cls.load_whitelisted_tools(),
            default_timeout=5.0
        )

    @classmethod 
    def load_from_file(cls, config_file: str) -> "Config":
        """Load configuration from JSON file, fall back to defaults if not found"""
        try:
            import json
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            tools = config_data.get('whitelisted_tools', cls.load_whitelisted_tools())
            timeout = config_data.get('default_timeout', 5.0)
            check_interval = config_data.get('check_interval', 1.0)
            enable_sleep_detection = config_data.get('enable_sleep_detection', False)
            
            return cls(
                whitelisted_tools=tools, 
                default_timeout=timeout,
                check_interval=check_interval,
                enable_sleep_detection=enable_sleep_detection
            )
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Return default config if file doesn't exist or is invalid
            return cls.get_default()