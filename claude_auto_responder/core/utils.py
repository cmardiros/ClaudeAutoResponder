"""Utility functions for Claude Auto Responder"""

from datetime import datetime

# Global configuration
LINES_TO_CAPTURE = 500


def _timestamp() -> str:
    """Generate timestamp string"""
    return datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "]"


def _extract_recent_text(text: str) -> str:
    """Extract recent lines from text for analysis with smart optimization"""
    return _extract_recent_text_smart(text)


def _extract_recent_text_smart(text: str) -> str:
    """
    Smart text extraction that tries to use fewer lines when possible.
    
    Conservative approach:
    1. Always ensure we have at least 50 lines for safety
    2. Check if we find clear prompt indicators in first 100 lines
    3. If not, use full 500 lines as fallback
    4. This is much safer than aggressive line reduction
    """
    lines = text.split('\n')
    if not lines:
        return ""
    
    total_lines = len(lines)
    
    # For small texts, just return everything
    if total_lines <= 100:
        return text
    
    # Try with 100 lines first (conservative)
    recent_100 = '\n'.join(lines[-100:])
    
    # Check for strong indicators that we have a complete prompt
    has_box_start = '╭─' in recent_100
    has_box_end = '╰─' in recent_100  
    has_option_marker = '❯' in recent_100
    has_do_you_want = 'do you want' in recent_100.lower()
    
    # If we have all the key indicators, 100 lines should be sufficient
    if has_box_start and has_box_end and has_option_marker and has_do_you_want:
        return recent_100
    
    # Try with 200 lines for medium-sized prompts
    if total_lines > 200:
        recent_200 = '\n'.join(lines[-200:])
        # Check again with more context
        has_box_start = '╭─' in recent_200
        has_box_end = '╰─' in recent_200  
        has_option_marker = '❯' in recent_200
        has_do_you_want = 'do you want' in recent_200.lower()
        
        if has_box_start and has_box_end and has_option_marker and has_do_you_want:
            return recent_200
    
    # Fallback to full 500 lines for safety
    return '\n'.join(lines[-LINES_TO_CAPTURE:])