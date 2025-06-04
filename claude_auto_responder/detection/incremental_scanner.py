"""Incremental bottom-up text scanner for maximum memory efficiency"""

from typing import Optional, Tuple
import re


class IncrementalScanner:
    """Memory-efficient incremental text scanner"""
    
    # Initial scan size - just enough to detect prompt ending
    INITIAL_SCAN_LINES = 50
    
    # Increment size when expanding upwards
    EXPANSION_INCREMENT = 100
    
    # Maximum lines to scan (prevents runaway expansion)
    MAX_SCAN_LINES = 2000
    
    # Patterns for quick detection
    BOX_BOTTOM_PATTERN = re.compile(r'╰─+╯')
    BOX_TOP_PATTERN = re.compile(r'╭─+╮')
    CARET_PATTERN = re.compile(r'❯\s*1\.\s*Yes')
    DO_YOU_WANT_PATTERN = re.compile(r'Do\s+you\s+want', re.IGNORECASE)
    
    @classmethod
    def find_prompt_window(cls, full_text: str, debug: bool = False) -> Optional[str]:
        """
        Efficiently find prompt window using incremental scanning.
        Returns only the relevant prompt text or None if no prompt found.
        """
        if not full_text:
            return None
            
        lines = full_text.split('\n')
        total_lines = len(lines)
        
        # Start with minimal scan from bottom
        scan_size = min(cls.INITIAL_SCAN_LINES, total_lines)
        
        if debug:
            print(f"[Scanner] Starting with {scan_size} lines from bottom (total: {total_lines})")
        
        while scan_size <= min(cls.MAX_SCAN_LINES, total_lines):
            # Get current scan window from bottom
            scan_start = max(0, total_lines - scan_size)
            scan_window = '\n'.join(lines[scan_start:])
            
            # Quick check: Do we have prompt ending indicators?
            has_box_bottom = bool(cls.BOX_BOTTOM_PATTERN.search(scan_window))
            has_caret = bool(cls.CARET_PATTERN.search(scan_window))
            
            if debug and scan_size == cls.INITIAL_SCAN_LINES:
                print(f"[Scanner] Initial scan - Box bottom: {has_box_bottom}, Caret: {has_caret}")
            
            # No prompt indicators? Stop here and return None
            if not has_box_bottom or not has_caret:
                if scan_size == cls.INITIAL_SCAN_LINES:
                    # First scan found nothing - definitely no prompt
                    if debug:
                        print("[Scanner] No prompt indicators in initial scan - stopping")
                    return None
                else:
                    # We were expanding but lost the indicators - shouldn't happen
                    if debug:
                        print(f"[Scanner] Lost indicators at {scan_size} lines - stopping")
                    return None
            
            # We have ending indicators - check if we have a complete box
            has_box_top = bool(cls.BOX_TOP_PATTERN.search(scan_window))
            has_do_you_want = bool(cls.DO_YOU_WANT_PATTERN.search(scan_window))
            
            if has_box_top and has_do_you_want:
                # Found complete prompt! Extract just the box
                box_content = cls._extract_box_content(scan_window)
                if debug:
                    print(f"[Scanner] Found complete prompt at {scan_size} lines")
                return box_content
            
            # Need more context - expand upwards
            if scan_size >= min(cls.MAX_SCAN_LINES, total_lines):
                if debug:
                    print(f"[Scanner] Reached scan limit ({scan_size} lines) - stopping")
                return None
                
            # Expand by increment
            old_size = scan_size
            scan_size = min(scan_size + cls.EXPANSION_INCREMENT, cls.MAX_SCAN_LINES, total_lines)
            
            if debug:
                print(f"[Scanner] Expanding from {old_size} to {scan_size} lines")
        
        return None
    
    @classmethod
    def _extract_box_content(cls, text: str) -> str:
        """Extract just the Claude box content from text"""
        lines = text.split('\n')
        
        # Find the last complete box (in case there are multiple)
        box_start = -1
        box_end = -1
        
        for i in range(len(lines) - 1, -1, -1):
            if cls.BOX_BOTTOM_PATTERN.match(lines[i].strip()) and box_end == -1:
                box_end = i
            elif cls.BOX_TOP_PATTERN.match(lines[i].strip()) and box_end != -1:
                box_start = i
                break
        
        if box_start != -1 and box_end != -1:
            # Return just the box content plus a few lines of context
            context_start = max(0, box_start - 5)
            context_end = min(len(lines), box_end + 5)
            return '\n'.join(lines[context_start:context_end])
        
        # Fallback - return last 200 lines if box extraction failed
        return '\n'.join(lines[-200:])