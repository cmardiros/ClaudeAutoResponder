#!/usr/bin/env swift

import Cocoa

/// Virtual key codes for common keys
enum VirtualKeyCode: CGKeyCode {
    case enter = 0x24      // Return key
    case downArrow = 0x7D  // Down arrow key
    case key2 = 0x13       // Number 2 key
}

/// Send a key press event
/// - Parameters:
///   - keyCode: The virtual key code to send
///   - delay: Delay between key down and up events (default: 0.01 seconds)
func sendKeyPress(_ keyCode: VirtualKeyCode, delay: TimeInterval = 0.01) {
    let keyDown = CGEvent(keyboardEventSource: nil, virtualKey: keyCode.rawValue, keyDown: true)
    let keyUp = CGEvent(keyboardEventSource: nil, virtualKey: keyCode.rawValue, keyDown: false)
    
    keyDown?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: delay)
    keyUp?.post(tap: .cghidEventTap)
}

/// Send the Enter key
func sendEnterKey() {
    sendKeyPress(.enter)
}

/// Send the Down Arrow key
func sendDownArrow() {
    sendKeyPress(.downArrow)
}

/// Send the number 2 key
func sendKey2() {
    sendKeyPress(.key2)
}

// Main execution
if CommandLine.arguments.count < 2 {
    print("Usage: send_keys.swift <key>")
    print("Available keys: 2, down, enter")
    exit(1)
}

let key = CommandLine.arguments[1].lowercased()

switch key {
case "2":
    print("Sending key '2'")
    sendKey2()
case "down":
    print("Sending down arrow")
    sendDownArrow()
case "enter", "return":
    print("Sending enter")
    sendEnterKey()
default:
    print("Unknown key: \(key)")
    print("Available keys: 2, down, enter")
    exit(1)
}

print("Key sent successfully")