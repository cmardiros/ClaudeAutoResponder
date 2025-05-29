#!/usr/bin/env python3
"""
Test suite for AutoResponder main functionality
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_auto_responder.core.responder import AutoResponder
from claude_auto_responder.config.settings import Config
from claude_auto_responder.models.prompt import ClaudePrompt


class TestAutoResponder(unittest.TestCase):
    """Test cases for the AutoResponder class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config.get_default()
        self.responder = AutoResponder(self.config, debug=False)

    def test_initialization(self):
        """Test AutoResponder initialization"""
        self.assertIsInstance(self.responder.config, Config)
        self.assertFalse(self.responder.running)
        self.assertFalse(self.responder.is_in_countdown)

    @patch('claude_auto_responder.platform.macos.subprocess.run')
    def test_send_response_option1(self, mock_subprocess):
        """Test sending response for option 1"""
        mock_subprocess.return_value.returncode = 0
        self.responder._send_response("1")
        
        # Should call enter to confirm
        mock_subprocess.assert_called_with(
            ['swift', '/Users/fahad/Developer/ClaudeAutoResponder/send_keys.swift', 'enter'],
            capture_output=True, text=True, timeout=5
        )

    @patch('claude_auto_responder.platform.macos.subprocess.run')
    def test_send_response_option2(self, mock_subprocess):
        """Test sending response for option 2"""
        mock_subprocess.return_value.returncode = 0
        self.responder._send_response("2")
        
        # Should call option 2 key then enter
        expected_calls = [
            unittest.mock.call(['swift', '/Users/fahad/Developer/ClaudeAutoResponder/send_keys.swift', '2'], 
                              capture_output=True, text=True, timeout=5),
            unittest.mock.call(['swift', '/Users/fahad/Developer/ClaudeAutoResponder/send_keys.swift', 'enter'], 
                              capture_output=True, text=True, timeout=5)
        ]
        mock_subprocess.assert_has_calls(expected_calls)

    def test_handle_claude_prompt(self):
        """Test handling of detected Claude prompt"""
        prompt = ClaudePrompt(
            is_valid=True,
            detected_tool="Edit file",
            has_option2=True
        )
        
        self.responder._handle_claude_prompt(prompt)
        
        # Should start countdown
        self.assertTrue(self.responder.is_in_countdown)
        self.assertIsNotNone(self.responder.countdown_prompt)
        self.assertEqual(self.responder.countdown_prompt, prompt)

    def test_cancel_countdown(self):
        """Test countdown cancellation"""
        self.responder.is_in_countdown = True
        self.responder._cancel_countdown("Test reason")
        
        self.assertFalse(self.responder.is_in_countdown)

    def test_stop_monitoring(self):
        """Test stop monitoring functionality"""
        self.responder.running = True
        
        with patch('builtins.print') as mock_print:
            self.responder.stop_monitoring()
        
        self.assertFalse(self.responder.running)
        mock_print.assert_called_once()


if __name__ == '__main__':
    unittest.main()