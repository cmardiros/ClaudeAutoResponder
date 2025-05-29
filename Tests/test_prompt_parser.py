#!/usr/bin/env python3
"""
Test suite for Prompt Parser functionality
"""

import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_auto_responder.detection.parser import PromptParser
from claude_auto_responder.models.prompt import ClaudePrompt
from claude_auto_responder.config.settings import Config


class TestClaudePromptDataclass(unittest.TestCase):
    """Test cases for the ClaudePrompt dataclass"""
    
    def test_default_prompt(self):
        """Test default ClaudePrompt values"""
        prompt = ClaudePrompt()
        
        self.assertFalse(prompt.is_valid)
        self.assertFalse(prompt.has_do_you_want)
        self.assertFalse(prompt.has_caret_on_option1)
        self.assertFalse(prompt.has_option2)
        self.assertFalse(prompt.has_box_structure)
        self.assertIsNone(prompt.detected_tool)
        self.assertEqual(prompt.option_to_select, "1")

    def test_prompt_with_option2(self):
        """Test prompt with option 2 available"""
        prompt = ClaudePrompt(has_option2=True)
        self.assertEqual(prompt.option_to_select, "2")


class TestConfig(unittest.TestCase):
    """Test cases for the Config class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = Config.get_default()
        
        self.assertIsInstance(config.whitelisted_tools, list)
        self.assertGreater(len(config.whitelisted_tools), 0)
        self.assertIn("Edit file", config.whitelisted_tools)
        self.assertIn("Bash command", config.whitelisted_tools)
        self.assertEqual(config.default_timeout, 5.0)
    
    def test_config_from_nonexistent_file(self):
        """Test loading config from non-existent file falls back to default"""
        config = Config.load_from_file("nonexistent_config.json")
        default_config = Config.get_default()
        
        self.assertEqual(config.whitelisted_tools, default_config.whitelisted_tools)
        self.assertEqual(config.default_timeout, default_config.default_timeout)


class TestPromptParser(unittest.TestCase):
    """Test cases for the PromptParser class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.default_tools = [
            "Read file", "Edit file", "Bash command", "Write", "MultiEdit", 
            "Grep", "Glob", "LS", "WebFetch", "WebSearch"
        ]
        self.parser = PromptParser(self.default_tools)

    def load_test_file(self, filename):
        """Load a test file from the resources directory"""
        test_dir = Path(__file__).parent / "resources"
        file_path = test_dir / filename
        
        if not file_path.exists():
            self.fail(f"Test file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_empty_content(self):
        """Test handling of empty content"""
        prompt = self.parser.parse_prompt("", debug=False)
        self.assertFalse(prompt.is_valid)

    def test_valid_edit_file_prompt(self):
        """Test parsing valid edit file prompt"""
        content = self.load_test_file("prompt_edit_file.txt")
        prompt = self.parser.parse_prompt(content, debug=False)
        
        self.assertTrue(prompt.is_valid, "Edit file prompt should be valid")
        self.assertTrue(prompt.has_do_you_want, "Should detect 'Do you want' text")
        self.assertTrue(prompt.has_caret_on_option1, "Should detect caret on option 1")
        self.assertEqual(prompt.detected_tool, "Edit file")

    def test_valid_long_edit_file_prompt(self):
        """Test parsing long edit file prompt with many lines"""
        content = self.load_test_file("prompt_long.txt")
        prompt = self.parser.parse_prompt(content, debug=False)
        
        self.assertTrue(prompt.is_valid, "Long edit file prompt should be valid")
        self.assertTrue(prompt.has_do_you_want, "Should detect 'Do you want' text")
        self.assertTrue(prompt.has_caret_on_option1, "Should detect caret on option 1")
        self.assertEqual(prompt.detected_tool, "Edit file")

    def test_valid_bash_command_standard(self):
        """Test parsing standard bash command prompt"""
        content = self.load_test_file("prompt_bash_command_standard.txt")
        prompt = self.parser.parse_prompt(content, debug=False)
        
        self.assertTrue(prompt.is_valid, "Bash command prompt should be valid")
        self.assertEqual(prompt.detected_tool, "Bash command")

    def test_invalid_bad_tool(self):
        """Test rejection of prompt with non-whitelisted tool"""
        content = self.load_test_file("prompt_invalid_bad_tool.txt")
        prompt = self.parser.parse_prompt(content, debug=False)
        
        self.assertFalse(prompt.is_valid, "Bad tool prompt should be invalid")

    def test_invalid_no_caret(self):
        """Test rejection of prompt without caret on option 1"""
        content = self.load_test_file("prompt_invalid_no_caret.txt")
        prompt = self.parser.parse_prompt(content, debug=False)
        
        self.assertFalse(prompt.is_valid, "No caret prompt should be invalid")
        self.assertTrue(prompt.has_do_you_want, "Should detect 'Do you want' text")
        self.assertFalse(prompt.has_caret_on_option1, "Should not detect caret on option 1")

    def test_tool_detection_case_insensitive(self):
        """Test that tool detection is case insensitive"""
        test_content = """
╭─────────────────────────────────────────────────────────╮
│ EDIT FILE                                               │
│ Do you want to edit this file?                          │
│ ❯ 1. Yes                                               │
╰─────────────────────────────────────────────────────────╯
        """
        
        prompt = self.parser.parse_prompt(test_content, debug=False)
        self.assertTrue(prompt.is_valid, "Case insensitive tool detection should work")
        self.assertEqual(prompt.detected_tool, "Edit file")


if __name__ == '__main__':
    unittest.main()