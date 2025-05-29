#!/usr/bin/env python3
"""
Test suite for Terminal Detection functionality
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_auto_responder.detection.terminal import TerminalDetector


class TestTerminalDetector(unittest.TestCase):
    """Test cases for the TerminalDetector class"""
    
    def test_terminal_bundle_ids(self):
        """Test that all expected terminal bundle IDs are present"""
        expected_terminals = {
            'com.apple.Terminal',
            'com.googlecode.iterm2', 
            'dev.warp.Warp-Stable',
            'co.zeit.hyper',
            'com.github.wez.wezterm',
            'net.kovidgoyal.kitty',
            'io.alacritty',
            'com.tabby.app',
            'com.termius-dmg',
            'com.mitchellh.ghostty'
        }
        
        self.assertEqual(TerminalDetector.TERMINAL_BUNDLE_IDS, expected_terminals)
        self.assertGreater(len(TerminalDetector.TERMINAL_BUNDLE_IDS), 5, 
                          "Should support multiple terminal applications")
    
    @patch('claude_auto_responder.detection.terminal.NSAppleScript')
    def test_get_frontmost_app_success(self, mock_applescript):
        """Test successful retrieval of frontmost app"""
        mock_script = MagicMock()
        mock_result = MagicMock()
        mock_result.stringValue.return_value = "com.apple.Terminal"
        mock_script.executeAndReturnError_.return_value = (mock_result, None)
        mock_applescript.alloc().initWithSource_.return_value = mock_script
        
        result = TerminalDetector.get_frontmost_app()
        self.assertEqual(result, "com.apple.Terminal")

    @patch.object(TerminalDetector, 'get_frontmost_app')
    def test_is_terminal_focused_true(self, mock_get_frontmost):
        """Test terminal focus detection when terminal is focused"""
        mock_get_frontmost.return_value = "com.apple.Terminal"
        
        result = TerminalDetector.is_terminal_focused()
        self.assertTrue(result)

    @patch.object(TerminalDetector, 'get_frontmost_app')
    def test_is_terminal_focused_false(self, mock_get_frontmost):
        """Test terminal focus detection when non-terminal is focused"""
        mock_get_frontmost.return_value = "com.apple.Finder"
        
        result = TerminalDetector.is_terminal_focused()
        self.assertFalse(result)

    @patch('claude_auto_responder.detection.terminal.NSAppleScript')
    def test_get_window_text_success(self, mock_applescript):
        """Test successful window text retrieval"""
        mock_script = MagicMock()
        mock_result = MagicMock()
        mock_result.stringValue.return_value = "Sample terminal text"
        
        mock_script.executeAndReturnError_.return_value = (mock_result, None)
        mock_applescript.alloc.return_value.initWithSource_.return_value = mock_script
        
        result = TerminalDetector.get_window_text()
        self.assertEqual(result, "Sample terminal text")


class TestTerminalDetectorIntegration(unittest.TestCase):
    """Integration tests for TerminalDetector (requires macOS)"""
    
    def test_detector_instantiation(self):
        """Test that TerminalDetector can be instantiated"""
        detector = TerminalDetector()
        self.assertIsInstance(detector, TerminalDetector)


if __name__ == '__main__':
    unittest.main()