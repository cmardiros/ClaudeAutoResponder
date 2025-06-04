#!/usr/bin/env python3
"""Monitor memory usage of Claude Auto Responder in real-time"""

import time
import psutil
import subprocess
import sys
import os
from datetime import datetime


def get_python_processes():
    """Find all Python processes running claude_auto_responder"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('claude_auto_responder' in str(arg) for arg in cmdline):
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def format_bytes(bytes_value):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def monitor_memory():
    """Monitor memory usage of Claude Auto Responder"""
    print("🔍 Monitoring memory usage of Claude Auto Responder...")
    print("Press Ctrl+C to stop\n")
    
    # Track peak memory
    peak_memory = 0
    start_time = time.time()
    
    try:
        while True:
            processes = get_python_processes()
            
            if not processes:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] No Claude Auto Responder process found. Waiting...", end='', flush=True)
            else:
                for proc in processes:
                    try:
                        # Get memory info
                        memory_info = proc.memory_info()
                        current_memory = memory_info.rss
                        peak_memory = max(peak_memory, current_memory)
                        
                        # Get CPU usage
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        
                        # Calculate uptime
                        uptime = time.time() - start_time
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        seconds = int(uptime % 60)
                        
                        # Display info
                        output = (
                            f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                            f"PID: {proc.pid} | "
                            f"Memory: {format_bytes(current_memory)} | "
                            f"Peak: {format_bytes(peak_memory)} | "
                            f"CPU: {cpu_percent:.1f}% | "
                            f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}"
                        )
                        
                        print(output + " " * 10, end='', flush=True)
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n📊 Final Statistics:")
        print(f"   Peak memory usage: {format_bytes(peak_memory)}")
        print(f"   Total monitoring time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        if peak_memory > 1024 * 1024 * 1024:  # > 1GB
            print("\n⚠️  Warning: Peak memory usage exceeded 1GB!")
            print("   This might indicate a memory leak.")
        else:
            print("\n✅ Memory usage appears normal.")


def run_test_scenario():
    """Run a test scenario to verify memory efficiency"""
    print("\n🧪 Running memory efficiency test...")
    print("This will simulate heavy terminal output and monitor memory usage.\n")
    
    # Start the auto responder in a subprocess
    print("Starting Claude Auto Responder...")
    responder_process = subprocess.Popen(
        [sys.executable, '-m', 'claude_auto_responder', '--debug'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(2)  # Let it initialize
    
    try:
        # Monitor for 60 seconds while simulating activity
        print("Monitoring memory for 60 seconds...")
        
        for i in range(60):
            # Get process memory
            try:
                proc = psutil.Process(responder_process.pid)
                memory_mb = proc.memory_info().rss / 1024 / 1024
                print(f"\r[{i+1}/60s] Memory: {memory_mb:.1f} MB", end='', flush=True)
            except psutil.NoSuchProcess:
                print("\nProcess ended unexpectedly!")
                break
            
            time.sleep(1)
        
        print("\n\n✅ Test completed!")
        
    finally:
        responder_process.terminate()
        responder_process.wait()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Claude Auto Responder memory usage')
    parser.add_argument('--test', action='store_true', help='Run test scenario')
    args = parser.parse_args()
    
    if args.test:
        run_test_scenario()
    else:
        monitor_memory()