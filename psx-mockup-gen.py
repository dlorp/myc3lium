#!/usr/bin/env python3
"""
PSX-Style UI Mockup Generator
Quick ASCII art generator for visualizing TUI/UI concepts
Inspired by PlayStation 1 menu aesthetics
"""

import sys
from typing import List, Tuple

# PSX-inspired color palette (ANSI codes)
COLORS = {
    'blue': '\033[94m',      # PSX blue
    'cyan': '\033[96m',      # Highlight
    'white': '\033[97m',     # Text
    'gray': '\033[90m',      # Disabled
    'green': '\033[92m',     # Success
    'yellow': '\033[93m',    # Warning
    'red': '\033[91m',       # Error
    'reset': '\033[0m',
    'bold': '\033[1m',
    'dim': '\033[2m',
}

# Box drawing characters
BOX = {
    'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
    'h': '─', 'v': '│',
    'lt': '├', 'rt': '┤', 'tt': '┬', 'bt': '┴', 'cross': '┼',
}

def box(width: int, height: int, title: str = "", color: str = 'blue') -> List[str]:
    """Generate a box with optional title"""
    lines = []
    c = COLORS[color]
    r = COLORS['reset']
    
    # Top border
    if title:
        title_padded = f" {title} "
        remaining = width - len(title_padded) - 2
        left_pad = remaining // 2
        right_pad = remaining - left_pad
        top = f"{c}{BOX['tl']}{BOX['h'] * left_pad}{title_padded}{BOX['h'] * right_pad}{BOX['tr']}{r}"
    else:
        top = f"{c}{BOX['tl']}{BOX['h'] * (width - 2)}{BOX['tr']}{r}"
    lines.append(top)
    
    # Empty lines
    for _ in range(height - 2):
        lines.append(f"{c}{BOX['v']}{r}{' ' * (width - 2)}{c}{BOX['v']}{r}")
    
    # Bottom border
    bottom = f"{c}{BOX['bl']}{BOX['h'] * (width - 2)}{BOX['br']}{r}"
    lines.append(bottom)
    
    return lines

def panel_split(width: int, height: int, left_title: str, right_title: str, 
                split_ratio: float = 0.5) -> List[str]:
    """Generate a two-panel layout"""
    lines = []
    c_blue = COLORS['blue']
    c_cyan = COLORS['cyan']
    r = COLORS['reset']
    
    left_width = int((width - 3) * split_ratio)
    right_width = width - left_width - 3
    
    # Top border with titles
    left_title_pad = f" {left_title} "
    right_title_pad = f" {right_title} "
    
    left_remaining = left_width - len(left_title_pad)
    left_left = left_remaining // 2
    left_right = left_remaining - left_left
    
    right_remaining = right_width - len(right_title_pad)
    right_left = right_remaining // 2
    right_right = right_remaining - right_left
    
    top = (f"{c_blue}{BOX['tl']}{BOX['h'] * left_left}{left_title_pad}{BOX['h'] * left_right}"
           f"{BOX['tt']}{BOX['h'] * right_left}{right_title_pad}{BOX['h'] * right_right}{BOX['tr']}{r}")
    lines.append(top)
    
    # Content rows
    for _ in range(height - 2):
        lines.append(f"{c_blue}{BOX['v']}{r}{' ' * left_width}{c_blue}{BOX['v']}{r}{' ' * right_width}{c_blue}{BOX['v']}{r}")
    
    # Bottom border
    bottom = (f"{c_blue}{BOX['bl']}{BOX['h'] * left_width}{BOX['bt']}{BOX['h'] * right_width}{BOX['br']}{r}")
    lines.append(bottom)
    
    return lines

def menu_items(items: List[Tuple[str, str]], selected: int = 0, 
               width: int = 40, show_indicator: bool = True) -> List[str]:
    """Generate menu item list with selection indicator"""
    lines = []
    c_cyan = COLORS['cyan']
    c_white = COLORS['white']
    c_gray = COLORS['gray']
    r = COLORS['reset']
    bold = COLORS['bold']
    
    for i, (label, status) in enumerate(items):
        indicator = "▶" if show_indicator and i == selected else " "
        
        if i == selected:
            # Highlighted item
            line = f"{c_cyan}{bold}{indicator} {label:<{width-4}}{r} {c_white}{status}{r}"
        else:
            # Normal item
            line = f"{c_gray}{indicator} {label:<{width-4}}{r} {c_gray}{status}{r}"
        
        lines.append(line)
    
    return lines

def status_bar(left_text: str, right_text: str, width: int = 80) -> str:
    """Generate a status bar footer"""
    c_blue = COLORS['blue']
    c_white = COLORS['white']
    r = COLORS['reset']
    bold = COLORS['bold']
    
    padding = width - len(left_text) - len(right_text) - 2
    return f"{c_blue}{bold}{left_text}{' ' * padding}{right_text}{r}"

def demo_dashboard():
    """Generate a demo automotive dashboard mockup"""
    print("\n" + "="*80)
    print("PSX-Style Automotive Dashboard Mockup")
    print("="*80 + "\n")
    
    # Split panel layout
    layout = panel_split(78, 16, "VEHICLE INFO", "SERVICE HISTORY")
    
    # Left panel content (vehicle info + upcoming)
    left_content = [
        "  2000 Subaru Legacy Outback",
        "  EJ22 • 157,340 mi • 23 MPG avg",
        "",
        "  ▼ UPCOMING SERVICE",
        "  🟢 Oil Change          +1,660 mi",
        "  🟡 Air Filter          +  340 mi",
        "  🟢 Coolant Flush       +8,660 mi",
        "  🟢 Spark Plugs        +18,660 mi",
    ]
    
    # Right panel content (service log)
    right_content = [
        "  2026-03-15  Oil Change @ 155,680 mi",
        "  2026-03-01  Tire Rotation @ 155,200 mi",
        "  2026-02-10  Brake Pads @ 154,100 mi",
        "  2026-01-20  Battery @ 153,500 mi",
        "  2025-12-15  Alternator @ 151,200 mi",
        "  2025-11-28  Oil Change @ 150,680 mi",
    ]
    
    # Overlay content on layout
    for i, line in enumerate(layout):
        if i == 0 or i == len(layout) - 1:
            # Border lines
            print(line)
        else:
            # Content lines
            row = i - 1
            left = f"  {left_content[row]:<30}" if row < len(left_content) else "  " + " " * 30
            right = f"  {right_content[row]:<38}" if row < len(right_content) else "  " + " " * 38
            
            # Reconstruct line with content
            c_blue = COLORS['blue']
            r = COLORS['reset']
            content_line = f"{c_blue}│{r}{left}{c_blue}│{r}{right}{c_blue}│{r}"
            print(content_line)
    
    # Status bar
    footer = status_bar("L:Log  R:Refresh  Q:Quit", "Session: a95d58ec", 78)
    print("\n" + footer)
    print()

def demo_menu():
    """Generate a demo menu mockup"""
    print("\n" + "="*80)
    print("PSX-Style Menu Mockup")
    print("="*80 + "\n")
    
    # Main box
    box_lines = box(50, 12, "MAIN MENU", "blue")
    
    # Menu items
    items = [
        ("New Game", ">"),
        ("Continue", ""),
        ("Options", ""),
        ("Gallery", "🔒"),
        ("Exit", ""),
    ]
    menu = menu_items(items, selected=0, width=46)
    
    # Overlay menu on box
    for i, line in enumerate(box_lines):
        if i == 0 or i == len(box_lines) - 1:
            print("  " + line)
        else:
            row = i - 1
            if row < len(menu):
                # Replace box content with menu item
                c_blue = COLORS['blue']
                r = COLORS['reset']
                print(f"  {c_blue}│{r}  {menu[row]:<44}  {c_blue}│{r}")
            else:
                print("  " + line)
    
    # Status bar
    footer = status_bar("↑↓:Select  ⏎:Confirm  ESC:Back", "v1.0.0", 50)
    print("\n  " + footer)
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "menu":
        demo_menu()
    else:
        demo_dashboard()
        print("\nTry: python psx-mockup-gen.py menu")
