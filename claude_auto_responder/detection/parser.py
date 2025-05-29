"""Claude prompt parsing logic"""

import re
from typing import List, Optional

from ..models.prompt import ClaudePrompt
from ..core.utils import _timestamp, _extract_recent_text, LINES_TO_CAPTURE


class PromptParser:
    """Parses terminal text to detect Claude prompts"""
    
    def __init__(self, whitelisted_tools: List[str]):
        self.whitelisted_tools = whitelisted_tools
        self.box_top_pattern = re.compile(r'^\s*╭─+╮', re.MULTILINE)
        self.box_bottom_pattern = re.compile(r'^\s*╰─+╯', re.MULTILINE)
        self.box_side_pattern = re.compile(r'^\s*│.*│', re.MULTILINE)
        self.do_you_want_pattern = re.compile(r'Do\s+you\s+want', re.IGNORECASE)
        self.caret_option1_pattern = re.compile(r'❯\s*1\.\s*Yes', re.MULTILINE)
        self.option2_pattern = re.compile(r'2\.\s*Yes,?\s*and\s*don\'?t\s*ask\s*again', re.MULTILINE | re.IGNORECASE)

    def parse_prompt(self, text: str, debug: bool = False) -> ClaudePrompt:
        """Parse text to detect valid Claude prompt - ONLY within complete box structures"""
        if not text:
            if debug:
                print(f"{_timestamp()} 🔍 DEBUG: No text provided to parse_prompt")
            return ClaudePrompt()

        # Extract recent lines for analysis
        recent_text = _extract_recent_text(text)
        capture_lines = LINES_TO_CAPTURE

        prompt = ClaudePrompt()

        if debug:
            print(f"{_timestamp()} 🔍 DEBUG: Starting prompt analysis on {len(text.split('\n'))} total lines, using last {capture_lines} lines ({len(recent_text)} chars)")

        # Check for basic elements
        do_you_want_match = self.do_you_want_pattern.search(recent_text)
        caret_option1_match = self.caret_option1_pattern.search(recent_text)
        
        prompt.has_do_you_want = bool(do_you_want_match)
        prompt.has_caret_on_option1 = bool(caret_option1_match)

        if debug:
            self._debug_prompt_elements(recent_text, do_you_want_match, caret_option1_match)

        # Extract boxes if basic elements are present
        if prompt.has_do_you_want and prompt.has_caret_on_option1:
            if debug:
                print(f"{_timestamp()} 🔍 DEBUG: Basic elements found, proceeding with box extraction...")
            
            # Find all complete Claude boxes in the text
            claude_boxes = self._extract_claude_boxes(recent_text)
            
            if debug:
                print(f"  - Found {len(claude_boxes)} complete Claude box structure(s)")
                for i, box in enumerate(claude_boxes):
                    print(f"    Box {i+1} content preview (first 200 chars): {repr(box[:200])}")
            
            # Look for a valid prompt within any of the boxes
            for i, box_content in enumerate(claude_boxes):
                if debug:
                    print(f"  - Validating box {i+1} content...")
                if self._validate_box_content(box_content, prompt, debug):
                    if debug:
                        print(f"    ✅ Box {i+1} contains valid prompt!")
                    prompt.is_valid = True
                    break
                elif debug:
                    print(f"    ❌ Box {i+1} validation failed")
        else:
            if debug:
                print(f"{_timestamp()} 🔍 DEBUG: Skipping box extraction - missing basic elements:")
                print(f"  - Has 'Do you want': {prompt.has_do_you_want}")
                print(f"  - Has '❯ 1. Yes': {prompt.has_caret_on_option1}")
            
            # Extract boxes for debug info
            claude_boxes = self._extract_claude_boxes(recent_text)

        if debug:
            print(f"{_timestamp()} 🔍 DEBUG: Final result - Valid: {prompt.is_valid}, Tool: {prompt.detected_tool}")

        return prompt

    def _extract_claude_boxes(self, text: str) -> List[str]:
        """Extract complete Claude Code box structures from text"""
        boxes = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            # Look for box top
            if self.box_top_pattern.match(lines[i]):
                box_start = i
                box_lines = [lines[i]]
                nested_level = 1  # Track nesting level for nested boxes
                i += 1
                
                # Collect box content until we find the matching bottom
                while i < len(lines):
                    box_lines.append(lines[i])
                    
                    # If we find another box top, increase nesting level
                    if self.box_top_pattern.match(lines[i]):
                        nested_level += 1
                    # If we find a box bottom, decrease nesting level
                    elif self.box_bottom_pattern.match(lines[i]):
                        nested_level -= 1
                        # If we're back to level 0, we found the matching bottom
                        if nested_level == 0:
                            box_content = '\n'.join(box_lines)
                            boxes.append(box_content)
                            break
                    
                    # Safety check to prevent infinite loops (use same limit as global line capture)
                    if len(box_lines) > LINES_TO_CAPTURE:
                        break
                        
                    i += 1
            else:
                i += 1
        
        return boxes

    def _debug_prompt_elements(self, recent_text: str, do_you_want_match, caret_option1_match):
        """Debug helper for showing prompt element detection results"""
        print(f"{_timestamp()} 🔍 DEBUG: Initial quick check results:")
        print(f"  - Searching for 'Do you want' pattern (case insensitive)")
        if do_you_want_match:
            context_start = max(0, do_you_want_match.start() - 30)
            context_end = min(len(recent_text), do_you_want_match.end() + 30)
            context = recent_text[context_start:context_end].replace('\n', '\\n')
            print(f"    ✅ FOUND at position {do_you_want_match.start()}: {repr(context)}")
        else:
            print(f"    ❌ NOT FOUND - no 'Do you want' text detected")
            sample_lines = [line.strip() for line in recent_text.split('\n')[-20:] if line.strip()]
            print(f"    📝 Last 20 non-empty lines to check: {sample_lines}")
        
        print(f"  - Searching for caret option pattern: '❯\\s*1\\.\\s*Yes'")
        if caret_option1_match:
            context_start = max(0, caret_option1_match.start() - 30)
            context_end = min(len(recent_text), caret_option1_match.end() + 30)
            context = recent_text[context_start:context_end].replace('\n', '\\n')
            print(f"    ✅ FOUND at position {caret_option1_match.start()}: {repr(context)}")
        else:
            print(f"    ❌ NOT FOUND - no '❯ 1. Yes' pattern detected")
            option_like_lines = []
            for line in recent_text.split('\n'):
                if any(char in line for char in ['❯', '1.', 'Yes', '▶', '>', '•']):
                    option_like_lines.append(repr(line.strip()))
            if option_like_lines:
                print(f"    📝 Lines with option-like content: {option_like_lines[:5]}")
            else:
                print(f"    📝 No option-like content found in text")

    def _validate_box_content(self, box_content: str, prompt: ClaudePrompt, debug: bool = False) -> bool:
        """Validate that a box contains a proper Claude Code prompt"""
        if debug:
            print(f"    🔍 DEBUG: Validating box content ({len(box_content)} chars):")
        
        # Must have "Do you want" within the box
        do_you_want_match = self.do_you_want_pattern.search(box_content)
        box_has_do_you_want = bool(do_you_want_match)
        if debug:
            if do_you_want_match:
                print(f"      ✅ 'Do you want' found in box")
            else:
                print(f"      ❌ 'Do you want' NOT found in box")
        if not box_has_do_you_want:
            return False

        # Set box structure flag
        prompt.has_box_structure = True
        if debug:
            print(f"      ✅ Box structure confirmed")

        # Must have caret on option 1 within the box
        caret_match = self.caret_option1_pattern.search(box_content)
        box_has_caret_on_option1 = bool(caret_match)
        if debug:
            if caret_match:
                print(f"      ✅ '❯ 1. Yes' found in box")
            else:
                print(f"      ❌ '❯ 1. Yes' NOT found in box")
        if not box_has_caret_on_option1:
            return False

        # Check for option 2 within the box
        option2_match = self.option2_pattern.search(box_content)
        prompt.has_option2 = bool(option2_match)
        if debug:
            if option2_match:
                print(f"      ✅ Option 2 'don't ask again' found in box")
            else:
                print(f"      ℹ️ Option 2 'don't ask again' not found (will use option 1)")

        # Must have a whitelisted tool name within the box
        prompt.detected_tool = self._detect_tool_in_box(box_content, debug)
        if debug:
            if prompt.detected_tool:
                print(f"      ✅ Whitelisted tool detected: '{prompt.detected_tool}'")
            else:
                print(f"      ❌ No whitelisted tool found in box")
        if not prompt.detected_tool:
            return False

        return True

    def _detect_tool_in_box(self, box_content: str, debug: bool = False) -> Optional[str]:
        """Detect whitelisted tool within a specific box"""
        if debug:
            print(f"      🔍 DEBUG: Searching for whitelisted tools in box...")
            print(f"        Checking against {len(self.whitelisted_tools)} whitelisted tools")
        
        # Sort tools by length (longest first) to prioritize longer matches
        sorted_tools = sorted(self.whitelisted_tools, key=len, reverse=True)
        
        for tool in sorted_tools:
            if tool.lower() in box_content.lower():
                if debug:
                    print(f"        ✅ Found tool: '{tool}'")
                return tool
        
        if debug:
            print(f"        ❌ No whitelisted tools found")
            print(f"        Whitelisted tools: {self.whitelisted_tools}")
            # Show what text we're searching through
            box_text_preview = box_content.replace('\n', ' ').strip()[:200]
            print(f"        Box text to search: {repr(box_text_preview)}...")
        
        return None