# Technical Spike Investigation: VS Code Terminal Support Feasibility (v2)

## 1. INVESTIGATION SUMMARY
**Technical Question**: Can ClaudeAutoResponder reliably operate within VS Code integrated terminals with active Claude Code sessions?
**Investigation Trigger**: Multi-project workflow creates context switching overhead that VS Code integration could eliminate
**Expected Outcome**: Go/no-go decision with specific technical evidence for VS Code integration feasibility
**Timeline**: 1.5 days maximum - focused validation with proper test setup
**Process**: Electron (not "Visual Studio Code" in System Events)

## 2. INVESTIGATION SCOPE

### Critical Path Technical Questions (Must Answer All)
**CQ-1**: **Foreground Detection** - Can we extract terminal content from VS Code integrated terminal with active Claude Code session when VS Code is focused?
**CQ-2**: **Background Detection** - Can we extract terminal content from VS Code integrated terminal with active Claude Code session when VS Code is backgrounded?
**CQ-3**: **Multi-Tab Targeting** - Can we reliably target specific terminal tabs within VS Code and deliver keystrokes to correct tab?
**CQ-4**: **Prompt Detection Accuracy** - Does existing PromptParser detect real Claude Code prompts from VS Code terminal with same accuracy as standalone terminals?
**CQ-5**: **Complete Cycle Validation** - Can we complete full prompt→response cycle in VS Code terminal matching standalone behavior?

### Investigation Success Criteria
**BLOCKER TEST**: If any critical question fails, investigation stops - VS Code integration not viable

**CQ-1 Success**: Extract real Claude Code prompt content from focused VS Code terminal tab
**CQ-2 Success**: Extract real Claude Code prompt content from backgrounded VS Code terminal tab  
**CQ-3 Success**: Send keystrokes to correct VS Code terminal tab in multi-tab scenario
**CQ-4 Success**: Existing PromptParser detects real Claude Code prompts in VS Code terminal
**CQ-5 Success**: Complete prompt→response cycle in VS Code matches standalone terminal behavior

### Scope Boundaries
**In Scope**: Technical validation with real Claude Code sessions and proper test isolation
**Out of Scope**: Performance optimization, edge cases, VS Code extension development, cross-platform support

## 3. TEST SETUP REQUIREMENTS

### Prerequisites
- VS Code installed and accessible via AppleScript
- Claude Code CLI available and functional
- ClaudeAutoResponder accessibility permissions configured
- Test project directory available for Claude Code sessions

### Clean Test Environment Criteria
**Clean Test Definition**: Each test must start with:
1. **Fresh VS Code window** (no previous terminals or sessions)
2. **Single terminal tab** (unless testing multi-tab scenarios)
3. **Active Claude Code session** with confirmed prompt visible on screen
4. **No other terminal applications running** during test
5. **Known VS Code window state** (focused or backgrounded as required)

### Human Verification Checkpoints
**Setup Confirmation Required**: Human must confirm visual state before each test:
- "Is VS Code window open with integrated terminal visible?"
- "Is Claude Code running and showing a prompt on screen?"
- "Is the prompt clearly visible in the VS Code terminal tab?"
- "Are there any other terminal apps running that should be closed?"

## 4. DETAILED TEST METHODOLOGY

### Test Suite 1: CQ-1 - Foreground Detection (30 minutes)

#### Test 1.1: Basic Content Extraction
**Setup**:
1. Launch fresh VS Code window
2. Open integrated terminal (Cmd+` or Terminal menu)
3. Navigate to test project directory
4. Launch Claude Code: `claude code`
5. Start conversation to generate prompt
6. **Human Confirm**: "Can you see a Claude Code prompt box in VS Code terminal?"

**Test Execution**:
```bash
# Test AppleScript access to focused VS Code terminal
osascript -e 'tell application "System Events" to tell process "Electron" to get value of text area 1 of window 1'
```

**Success Criteria**: Extract text containing visible Claude Code prompt
**Failure Criteria**: Empty result, error, or content not matching screen

#### Test 1.2: Content Accuracy Validation  
**Setup**: Same as Test 1.1
**Test Execution**: Compare extracted content with human visual confirmation
**Human Confirm**: "Does the extracted text match what you see in VS Code terminal?"

**Success Criteria**: Extracted content matches visual prompt exactly
**Failure Criteria**: Content mismatch, truncation, or encoding issues

### Test Suite 2: CQ-2 - Background Detection (30 minutes)

#### Test 2.1: Background Content Extraction
**Setup**:
1. Complete Test 1.1 setup with visible Claude Code prompt
2. **Human Confirm**: "Claude Code prompt visible in VS Code?"
3. Focus different application (e.g., open Chrome/Safari)
4. **Human Confirm**: "VS Code is now in background, prompt still visible?"

**Test Execution**:
```bash
# Test AppleScript access to backgrounded VS Code terminal
osascript -e 'tell application "System Events" to tell process "Electron" to get value of text area 1 of window 1'
```

**Success Criteria**: Extract same Claude Code prompt content as foreground test
**Failure Criteria**: Empty result, permission error, or different content

#### Test 2.2: Background vs Foreground Comparison
**Setup**: Same as Test 2.1
**Test Execution**: Compare background extraction with foreground extraction results
**Success Criteria**: Identical content extracted in both states
**Failure Criteria**: Content differs between foreground/background states

### Test Suite 3: CQ-3 - Multi-Tab Targeting (45 minutes)

#### Test 3.1: Multi-Tab Setup and Identification
**Setup**:
1. Launch fresh VS Code window
2. Create 3 terminal tabs:
   - Tab 1: Basic shell prompt
   - Tab 2: Active Claude Code session with prompt
   - Tab 3: Basic shell prompt
3. **Human Confirm**: "Three terminal tabs visible? Claude Code prompt in tab 2?"

**Test Execution**:
```bash
# Test targeting specific tabs
osascript -e 'tell application "System Events" to tell process "Electron" to get UI elements of window 1'
```

**Success Criteria**: Identify distinct terminal tabs and target tab 2
**Failure Criteria**: Cannot distinguish tabs or target specific tab

#### Test 3.2: Keystroke Delivery to Correct Tab
**Setup**: Same as Test 3.1 with Claude Code prompt in tab 2
**Test Execution**:
1. Focus VS Code tab 2 (with Claude Code prompt)
2. **Human Confirm**: "Tab 2 focused with Claude Code prompt visible?"
3. Send test keystroke using existing send_keys.swift
4. **Human Confirm**: "Did keystroke appear in correct tab (tab 2)?"

**Success Criteria**: Keystroke delivered to correct tab with Claude Code session
**Failure Criteria**: Keystroke delivered to wrong tab or not delivered

### Test Suite 4: CQ-4 - Prompt Detection Accuracy (30 minutes)

#### Test 4.1: Real Prompt Parsing
**Setup**:
1. Complete Test 1.1 setup with active Claude Code prompt
2. Extract actual terminal content via AppleScript
3. **Human Confirm**: "Extracted content contains the visible prompt?"

**Test Execution**:
```python
# Use existing PromptParser against real VS Code terminal content
parser = PromptParser(whitelisted_tools=['Bash', 'Edit', 'Write', 'Read'])
result = parser.parse_prompt(extracted_vscode_content, debug=True)
```

**Success Criteria**: Parser detects valid prompt with correct tool and options
**Failure Criteria**: Parser fails to detect prompt or detects incorrectly

#### Test 4.2: Detection Accuracy Comparison
**Setup**: Create identical Claude Code session in standalone terminal (iTerm2/Terminal.app)
**Test Execution**: Compare PromptParser results between VS Code and standalone terminal
**Success Criteria**: Identical detection results between VS Code and standalone
**Failure Criteria**: Different detection results or accuracy

### Test Suite 5: CQ-5 - Complete Cycle Validation (45 minutes)

#### Test 5.1: End-to-End Response Delivery
**Setup**:
1. Fresh VS Code with active Claude Code prompt
2. **Human Confirm**: "Ready to test full response cycle?"

**Test Execution**:
1. Extract prompt via AppleScript
2. Parse prompt with PromptParser  
3. Send response keystroke via send_keys.swift
4. **Human Confirm**: "Did Claude Code accept the response correctly?"

**Success Criteria**: Complete cycle works identical to standalone terminal
**Failure Criteria**: Any step fails or behaves differently

#### Test 5.2: Multiple Cycle Validation
**Setup**: Same as Test 5.1
**Test Execution**: Repeat cycle 3 times with different prompts
**Success Criteria**: All cycles complete successfully
**Failure Criteria**: Any cycle fails or shows degraded performance

## 5. CLEAN TEST PROTOCOLS

### Between-Test Cleanup
**Required between each test**:
1. Close all VS Code windows
2. Terminate any running Claude Code sessions
3. Clear terminal history if needed
4. Restart VS Code fresh
5. **Human Confirm**: "Clean state confirmed for next test?"

### Test Isolation
**Per test requirements**:
- One VS Code window only
- Known terminal tab state
- Confirmed Claude Code session state
- No other terminal applications running
- Accessibility permissions confirmed working

### Failure Protocols
**If any test fails**:
1. Document exact error message/behavior
2. **Human Confirm**: "Can you describe what you observe on screen?"
3. Screenshot VS Code state if helpful
4. Clean environment before next test
5. Mark critical question as FAILED

## 6. TECHNICAL SPECIFICATIONS

### Known VS Code Properties
- **Bundle ID**: `com.microsoft.VSCode`
- **Process Name**: "Electron" (in System Events)
- **AppleScript Support**: Basic application control confirmed
- **Terminal Access**: Unknown (to be tested)

### Test Environment
- **macOS**: Required for AppleScript testing
- **VS Code**: Latest version
- **Claude Code CLI**: Functional installation
- **Terminal**: Integrated VS Code terminal only

## 7. SUCCESS/FAILURE DECISION FRAMEWORK

### GO Decision Criteria
**All 5 critical questions must PASS**:
- CQ-1: Foreground detection works ✅
- CQ-2: Background detection works ✅  
- CQ-3: Multi-tab targeting works ✅
- CQ-4: Prompt detection accuracy matches standalone ✅
- CQ-5: Complete cycle works ✅

### NO-GO Decision Criteria
**Any 1 critical question FAILS**:
- Document specific technical blocker
- Assess if blocker is addressable
- Consider alternative approaches
- Clear documentation of why VS Code integration not viable

## 8. DELIVERABLES

### Primary Deliverable
**Technical Feasibility Decision**: Clear GO/NO-GO with supporting evidence

### Supporting Documentation
**Test Results**: Pass/fail for each CQ-1 through CQ-5 with technical evidence
**Implementation Specification**: If feasible, exact code changes and effort estimate  
**Technical Blockers**: If not feasible, specific limitations preventing implementation
**Human Observations**: Documented visual confirmations and behaviors observed

## 9. INVESTIGATION EXECUTION PLAN

### Day 1 (6 hours)
**Morning (3 hours)**: 
- Test environment setup and CQ-1/CQ-2 validation
- **STOP GATE**: If foreground/background detection fails, assess if addressable

**Afternoon (3 hours)**:
- CQ-3/CQ-4 validation (multi-tab targeting and prompt detection)
- **STOP GATE**: If targeting or detection fails, investigation may end

### Day 2 (2 hours)
**Morning Only**:
- CQ-5 validation (complete cycle testing)
- Documentation of results and decision

### Acceptance Criteria
**Investigation Complete When**:
- All 5 critical questions tested with proper setup
- Human visual confirmations documented
- Clear GO/NO-GO decision with evidence
- Implementation plan or blocker documentation ready

---

## INVESTIGATION VALIDATION CHECKLIST
- [x] Real Claude Code sessions required for all tests
- [x] Human visual confirmation at each step
- [x] Clean test environment protocols defined
- [x] Process name corrected (Electron, not Visual Studio Code)
- [x] Multi-tab targeting scenarios included
- [x] Comparison with standalone terminal behavior
- [x] Clear failure criteria and stop gates
- [x] Between-test cleanup protocols defined