#!/usr/bin/env python3
"""
Test runner for Claude Auto Responder Python version
"""

import unittest
import sys
import os
from pathlib import Path

def main():
    """Run all tests"""
    print("🧪 Claude Auto Responder Python - Test Suite")
    print("=" * 50)
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True  # Capture print statements during tests
    )
    
    print(f"\n🔍 Discovered {suite.countTestCases()} test cases")
    print("Running tests...\n")
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.skipped:
        print("\n⏭️  SKIPPED:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())