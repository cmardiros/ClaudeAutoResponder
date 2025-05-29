"""Claude prompt data model"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClaudePrompt:
    """Represents a detected Claude prompt"""
    is_valid: bool = False
    has_do_you_want: bool = False
    has_caret_on_option1: bool = False
    has_option2: bool = False
    has_box_structure: bool = False
    detected_tool: Optional[str] = None
    
    @property
    def option_to_select(self) -> str:
        """Determine which option to select based on available options"""
        return "2" if self.has_option2 else "1"