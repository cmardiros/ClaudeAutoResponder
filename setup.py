#!/usr/bin/env python3
"""
Setup script for Claude Auto Responder
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages"""
    print("📦 Installing required Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", "requirements.txt"])
            print("✅ All packages installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            print("\n💡 Try installing manually:")
            print("  pip3 install --user pyobjc-framework-Cocoa")
            return False

def main():
    print("🤖 Claude Auto Responder Setup")
    print("==============================\n")
    
    if not install_requirements():
        sys.exit(1)
    
    # Make script executable
    try:
        os.chmod("claude_auto_responder.py", 0o755)
        print("✅ Made script executable")
    except Exception as e:
        print(f"❌ Failed to make script executable: {e}")
    
    print("\n🎉 Setup completed!")
    print("\n🚀 Usage:")
    print("  python3 claude_auto_responder.py")
    print("  python3 claude_auto_responder.py --delay 3")
    print("  python3 claude_auto_responder.py --debug")

if __name__ == "__main__":
    main()