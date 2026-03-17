"""
JARVIS CLI Display Functions
"""

import json
from typing import Optional


def display_chat(message: str, role: str = "assistant"):
    """Display a chat message"""
    prefix = "[JARVIS]" if role == "assistant" else "[You]"
    print(f"\n{prefix} {message}\n")


def display_error(message: str):
    """Display an error message"""
    print(f"\n✗ Error: {message}\n", file=__import__('sys').stderr)


def display_success(message: str):
    """Display a success message"""
    print(f"\n✓ {message}\n")


def display_memory(data: dict, title: str = "Memories"):
    """Display memory data in a formatted way"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)
    
    # Handle different response formats
    if "results" in data:
        items = data["results"]
        print(f"Found {len(items)} results\n")
        
        for i, item in enumerate(items, 1):
            content = item.get("content", "")[:100]
            entry_type = item.get("entry_type", "unknown")
            importance = item.get("importance", 0)
            
            print(f"{i}. [{entry_type}] (importance: {importance:.2f})")
            print(f"   {content}")
            print()
            
    elif "memories" in data:
        items = data["memories"]
        print(f"Found {len(items)} memories\n")
        
        for i, item in enumerate(items, 1):
            query = item.get("query", "")[:80]
            response = item.get("response", "")[:80]
            
            print(f"{i}. Q: {query}")
            print(f"   A: {response}")
            print()
    else:
        print(json.dumps(data, indent=2))
    
    print('='*60 + '\n')


def display_stats(data: dict):
    """Display system statistics"""
    print(f"\n{'='*60}")
    print(" System Statistics")
    print('='*60)
    
    # CPU
    cpu = data.get("cpu", {})
    cpu_pct = cpu.get("percent", "N/A")
    print(f"  CPU:      {cpu_pct}%")
    
    # Memory
    mem = data.get("memory", {})
    mem_used = mem.get("used_gb", 0)
    mem_total = mem.get("total_gb", 0)
    mem_pct = mem.get("percent", "N/A")
    print(f"  Memory:   {mem_used:.1f}GB / {mem_total:.1f}GB ({mem_pct}%)")
    
    # VRAM (optional)
    vram = data.get("vram")
    if vram:
        vram_used = vram.get("used_gb", 0)
        vram_total = vram.get("total_gb", 0)
        vram_pct = vram.get("percent", "N/A")
        print(f"  VRAM:     {vram_used:.1f}GB / {vram_total:.1f}GB ({vram_pct}%)")
    
    print('='*60 + '\n')


def display_table(headers: list[str], rows: list[list[str]]):
    """Display data as a table"""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print header
    print("  ".join(h.ljust(w) for h, w in zip(headers, col_widths)))
    print("  ".join("-" * w for w in col_widths))
    
    # Print rows
    for row in rows:
        print("  ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)))


def display_json(data: dict, indent: int = 2):
    """Display JSON data"""
    print(json.dumps(data, indent=indent))


def loading(message: str = "Loading..."):
    """Display loading message"""
    print(f"\n{message}", end="", flush=True)


def clear_loading():
    """Clear loading message"""
    print("\r" + " " * 50 + "\r", end="")
