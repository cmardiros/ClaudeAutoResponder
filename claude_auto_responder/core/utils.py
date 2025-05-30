"""Utility functions for Claude Auto Responder"""

from datetime import datetime
import re

# Global configuration
LINES_TO_CAPTURE = 500
INITIAL_LINES = 15
EXPANSION_STEP = 10
MAX_LINES = 500


def _timestamp() -> str:
    """Generate timestamp string"""
    return datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "]"


def _extract_recent_text(text: str) -> str:
    """Extract recent lines from text for analysis using dynamic expansion"""
    return _extract_recent_text_dynamic(text)


def _extract_recent_text_dynamic(text: str) -> str:
    """
    Dynamically extract text starting with fewer lines and expanding as needed.
    
    Algorithm:
    1. Start with last 15 lines
    2. Look for end of box (╰─╯) and option marker (❯ 1. Yes)
    3. If found, expand by 10 lines at a time up to 500 max
    4. Keep expanding until we find box start (╭─╮) and a tool name
    """
    lines = text.split('\n')
    if not lines:
        return ""
    
    total_lines = len(lines)
    current_lines = min(INITIAL_LINES, total_lines)
    
    # Regex patterns for box detection
    box_end_pattern = re.compile(r'^\s*╰─+╯\s*$', re.MULTILINE)
    box_start_pattern = re.compile(r'^\s*╭─+╮\s*$', re.MULTILINE)
    option_pattern = re.compile(r'❯\s*1\.\s*Yes', re.MULTILINE)
    
    while current_lines <= min(MAX_LINES, total_lines):
        # Get the current slice of lines
        recent_text = '\n'.join(lines[-current_lines:])
        
        # Check if we have the basic indicators of a prompt end
        has_box_end = bool(box_end_pattern.search(recent_text))
        has_option = bool(option_pattern.search(recent_text))
        
        if not (has_box_end and has_option):
            # If we don't have the basic end markers, expand immediately
            if current_lines >= total_lines:
                break
            current_lines = min(current_lines + EXPANSION_STEP, total_lines, MAX_LINES)
            continue
        
        # We have potential end markers, now check if we have a complete box
        has_box_start = bool(box_start_pattern.search(recent_text))
        
        if has_box_start:
            # We have a complete box structure, check if it contains recognizable tool content
            # Look for common tool indicators that suggest we have tool content
            tool_indicators = [
                'edit file', 'read file', 'bash', 'write', 'multiedit', 
                'grep', 'glob', 'ls', 'webfetch', 'websearch', 'task'
            ]
            
            has_tool_content = any(indicator in recent_text.lower() for indicator in tool_indicators)
            
            if has_tool_content:
                # We have a complete box with tool content, this should be sufficient
                return recent_text
        
        # If we don't have a complete box or tool content, keep expanding
        if current_lines >= total_lines or current_lines >= MAX_LINES:
            break
            
        current_lines = min(current_lines + EXPANSION_STEP, total_lines, MAX_LINES)
    
    # Fallback to current lines if we've reached the limit
    return '\n'.join(lines[-current_lines:])