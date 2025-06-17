# Claude Auto Responder - Repository Structure Overview

## 🗂️ Repository Structure Analysis

The ClaudeAutoResponder is a Python-based tool that automatically responds to Claude Code confirmation prompts on macOS. The repository follows a clean, modular structure with clear separation of concerns.

```
ClaudeAutoResponder/
├── LICENSE                           # MIT License
├── README.md                        # Project documentation
├── setup.py                         # Installation script
├── requirements.txt                 # Python dependencies
├── claude_auto_responder.py         # Main entry point script
├── whitelisted_tools.txt           # Tool configuration
├── monitor_memory.py               # Memory monitoring utility
├── run_tests.py                    # Test runner script
├── send_keys.swift                 # Swift code for keystroke sending
├── claude_auto_responder/          # Main package directory
├── Tests/                          # Test suite with resources
└── ai-docs-repo-analysis/          # AI documentation output
```

## 📁 Top-Level Directory Overview

### Core Directories

**claude_auto_responder/** (Priority: High)
- **Purpose:** Main Python package containing all application logic
- **Structure:** Organized into logical modules (cli, core, detection, models, platform, config)
- **Entry Point:** Contains the modular architecture for the auto-responder functionality

**Tests/** (Priority: Medium)
- **Purpose:** Comprehensive test suite with test resources
- **Structure:** Unit tests plus resource files containing sample prompts for testing
- **Coverage:** Tests for auto responder, memory efficiency, prompt parsing, and terminal detection

### Configuration & Setup Files

**Root Level Files** (Priority: High)
- `claude_auto_responder.py` - Main executable entry point
- `setup.py` - Installation and setup script with Python version checking
- `requirements.txt` - Single dependency: pyobjc-framework-Cocoa>=9.0
- `whitelisted_tools.txt` - Configuration file listing approved Claude tools

**Utility Files** (Priority: Low)
- `monitor_memory.py` - Memory usage monitoring utility
- `run_tests.py` - Test execution script
- `send_keys.swift` - Swift code for macOS keystroke simulation

## 🔍 Key Subdirectory Analysis

### **claude_auto_responder/** - Main Package Structure

```
claude_auto_responder/
├── __init__.py                 # Package initialization with version
├── cli.py                      # Command-line interface and argument parsing
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration management
├── core/
│   ├── __init__.py
│   ├── responder.py            # Main AutoResponder class
│   └── utils.py                # Utility functions
├── detection/
│   ├── __init__.py
│   ├── parser.py               # Prompt parsing logic
│   └── terminal.py             # Terminal window detection
├── models/
│   ├── __init__.py
│   └── prompt.py               # ClaudePrompt data model
└── platform/
    ├── __init__.py
    ├── macos.py                # macOS-specific keystroke handling
    └── sleep_detector.py       # System sleep/wake detection
```

### **Key Files Analysis**

#### **Entry Points**
```python
# claude_auto_responder.py - Main executable
#!/usr/bin/env python3
from claude_auto_responder.cli import main

if __name__ == "__main__":
    main()
```

#### **CLI Interface (cli.py)**
- Comprehensive argument parsing with argparse
- Support for delay, debug mode, tool filtering, and monitoring modes
- Configuration loading and validation
- macOS platform check

#### **Core Logic (core/responder.py)**
```python
class AutoResponder:
    """Main auto responder class"""
    
    def __init__(self, config: Config, debug: bool = False, monitor_all: bool = False):
        self.config = config
        self.parser = PromptParser(config.whitelisted_tools)
        self.detector = TerminalDetector()
        self.keystroke_sender = MacOSKeystrokeSender(debug)
        self.sleep_detector = SleepDetector()
```

#### **Prompt Detection (detection/parser.py)**
- Regex-based parsing for Claude prompt boxes
- Box structure detection using Unicode box-drawing characters
- Tool whitelist validation
- Handles "Yes" and "Yes, and don't ask again" options

### **Tests/** - Test Structure

```
Tests/
├── __init__.py
├── resources/                          # Test data files
│   ├── prompt_bash_command_dont_ask.txt
│   ├── prompt_bash_command_standard.txt
│   ├── prompt_edit_file.txt
│   ├── prompt_invalid_bad_tool.txt
│   ├── prompt_invalid_no_caret.txt
│   ├── prompt_long.txt
│   ├── prompt_read_files_standard.txt
│   └── prompt_search_mislabeled.txt
├── test_auto_responder.py              # Main functionality tests
├── test_memory_efficiency.py           # Memory usage tests
├── test_prompt_parser.py               # Parser logic tests
└── test_terminal_detector.py           # Terminal detection tests
```

## 📖 Documentation Hotspots

### **README Files**
- **Root README.md:** Primary project documentation with setup and usage instructions
- **Package __init__.py:** Version information and package metadata

### **Configuration Documentation**
- **whitelisted_tools.txt:** Well-commented configuration file with usage examples
- **CLI help:** Comprehensive help text with examples in cli.py

### **Code Documentation**
- Extensive docstrings throughout all modules
- Inline comments explaining complex logic, especially in parser.py
- Type hints used consistently across the codebase

### **Test Documentation**
- Test resource files provide examples of various prompt formats
- Test names clearly indicate what functionality is being tested

## 🎯 Navigation Recommendations

### **Start Here**
1. `README.md` - Project overview and setup instructions
2. `claude_auto_responder.py` - Main entry point
3. `claude_auto_responder/cli.py` - Command-line interface and options
4. `whitelisted_tools.txt` - Understanding tool configuration

### **Core Logic Flow**
1. `claude_auto_responder/core/responder.py` - Main monitoring loop
2. `claude_auto_responder/detection/terminal.py` - Terminal window detection
3. `claude_auto_responder/detection/parser.py` - Prompt parsing logic
4. `claude_auto_responder/platform/macos.py` - Keystroke sending

### **Extension Points**
- **New Tools:** Add to `whitelisted_tools.txt` or parser logic
- **New Platforms:** Extend platform/ directory with new OS support
- **New Prompt Formats:** Modify parser.py regex patterns
- **Configuration:** Extend config/settings.py

### **Testing Strategy**
- **Unit Tests:** Each major component has dedicated test files
- **Integration Tests:** test_auto_responder.py tests full workflow
- **Test Resources:** Realistic prompt examples in Tests/resources/
- **Memory Testing:** Dedicated memory efficiency testing

## 🏗️ Build & Configuration Structure

### **Build System**
```python
# setup.py - Custom installation script
def install_requirements():
    """Install required Python packages"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"])

def main():
    # Python version check (3.9+)
    # Package installation with fallback strategies
    # Script permissions setup
```

### **Environment Configuration**
- **Requirements:** Single dependency on pyobjc-framework-Cocoa for macOS integration
- **Python Version:** Requires Python 3.9+
- **Platform:** macOS-specific (uses Cocoa framework)

### **Dependencies**
```
# requirements.txt
pyobjc-framework-Cocoa>=9.0
```

### **Scripts & Automation**
- **setup.py:** Interactive setup with error handling and version checking
- **run_tests.py:** Test runner with proper Python path setup
- **monitor_memory.py:** Development utility for memory profiling

### **Configuration Management**
```python
# claude_auto_responder/config/settings.py
class Config:
    def __init__(self, whitelisted_tools: List[str] = None, 
                 default_timeout: float = 0.0,
                 enable_sleep_detection: bool = False):
        # Configuration with sensible defaults
        
    @staticmethod
    def load_whitelisted_tools(filename: str) -> List[str]:
        # File-based configuration loading
```

## 🔄 Application Flow

1. **Initialization:** CLI parsing → Configuration loading → Component setup
2. **Monitoring:** Terminal detection → Text capture → Prompt parsing
3. **Response:** Tool validation → Keystroke simulation → Cooldown period
4. **Loop:** Continuous monitoring with sleep/wake detection support

The architecture emphasizes modularity, testability, and platform-specific functionality while maintaining a clean separation between detection, parsing, and response logic.