# DRY Violation Analysis: Script Path Calculation Duplication

## Issue Summary

**Code Smell**: Path calculation logic for `send_keys.swift` is duplicated across production and test code, violating the Don't Repeat Yourself (DRY) principle.

**Impact**: Low immediate risk, but creates maintenance burden and potential for inconsistency.

## Current Duplication

### Location 1: Production Code
**File**: `claude_auto_responder/platform/macos.py:15-16`
```python
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
self.script_path = os.path.join(current_dir, "send_keys.swift")
```

### Location 2: Test Code (2 instances)
**File**: `Tests/test_auto_responder.py:41-44` and `57-60`
```python
expected_script_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "send_keys.swift"
)
```

**Key Difference**: Tests use 2 `dirname()` calls, production uses 3 (due to different file depths).

## Risk Assessment

### Current Risks (Low)
- **Maintenance**: Changes to project structure require updates in multiple places
- **Inconsistency**: Different dirname depths could lead to bugs if not carefully maintained
- **Test Brittleness**: Tests depend on implementation details rather than contracts

### Future Risks (Medium)
- **Refactoring Difficulty**: Moving Swift script location requires coordinated changes
- **Platform Expansion**: Adding Windows/Linux support would multiply this pattern
- **Test Reliability**: Implementation changes break tests unnecessarily

## Root Cause Analysis

**Why this happened**: 
1. Original code had hardcoded paths
2. Production code was fixed with dynamic calculation
3. Tests were updated to match, duplicating the logic
4. No abstraction was created during the fix

**This is technical debt** from an incremental fix rather than a systematic solution.

## Recommended Solutions (Priority Order)

### Option 1: Extract to Utility Function (Recommended)
**Approach**: Create shared utility for script path resolution
```python
# claude_auto_responder/core/utils.py
def get_swift_script_path(from_file: str) -> str:
    """Get absolute path to send_keys.swift from any project file"""
    # Calculate relative to project root
    project_root = # ... centralized logic
    return os.path.join(project_root, "send_keys.swift")
```

**Benefits**:
- Single source of truth
- Easy to test and validate
- Clear interface
- Supports future script location changes

### Option 2: Configuration-Based Path (Alternative)
**Approach**: Move script path to configuration
```python
# config/settings.py
SWIFT_SCRIPT_PATH = "send_keys.swift"  # relative to project root
```

**Benefits**:
- Configurable without code changes
- Environment-specific overrides possible
- Clear separation of concerns

### Option 3: Mock at Higher Level (Test-Only Fix)
**Approach**: Mock `MacOSKeystrokeSender` instead of subprocess calls
```python
@patch.object(AutoResponder, 'keystroke_sender')
def test_send_response_option1(self, mock_keystroke_sender):
    # Test behavior, not implementation
```

**Benefits**:
- Eliminates path dependencies in tests
- Tests actual interface contracts
- More robust to refactoring

## Implementation Plan

### Phase 1: Quick Win (Recommended for Next Sprint)
Implement **Option 3** (Higher-level mocking) to eliminate test duplication immediately:
- Replace subprocess mocking with keystroke_sender mocking
- Remove duplicated path calculation from tests
- Maintain production code as-is

**Effort**: 30 minutes  
**Risk**: Very low  
**Benefit**: Eliminates 2/3 of duplication immediately

### Phase 2: Complete Solution (Future Refactoring)
Implement **Option 1** (Utility function) for comprehensive fix:
- Extract path calculation to shared utility
- Update production code to use utility
- Add unit tests for path resolution logic
- Consider Option 2 for configuration-driven approach

**Effort**: 2-3 hours  
**Risk**: Low  
**Benefit**: Complete DRY compliance, better architecture

## Technical Debt Assessment

**Current Level**: Minor (Yellow)
- Code works correctly
- Duplication is limited and contained
- No immediate business impact

**Without Fix**: Could become Moderate (Orange)
- Project restructuring becomes complex
- Test maintenance burden increases
- Platform expansion hindered

## Recommendation

**Immediate Action**: Implement Phase 1 (higher-level test mocking)
**Future Planning**: Schedule Phase 2 for next major refactoring cycle

This follows the principle: "Make the change easy, then make the easy change."