"""Utility functions for Claude Auto Responder"""

from datetime import datetime

# Global configuration
LINES_TO_CAPTURE = 500


def _timestamp() -> str:
    """Generate timestamp string"""
    return datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "]"


def _extract_recent_text(text: str) -> str:
    """Extract recent lines from text for analysis"""
    lines = text.split('\n')
    return '\n'.join(lines[-LINES_TO_CAPTURE:])