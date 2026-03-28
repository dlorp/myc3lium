#!/usr/bin/env python3
"""
plasma-field.py — Classic plasma field demoscene effect (ASCII)

Generates real-time plasma field visualization using sine waves
and color interpolation. Classic demoscene technique from 1990s.

Features:
- Multiple sine wave interference patterns
- 256-color palette (PSX aesthetic)
- Frame-by-frame animation
- Color cycling
- ASCII character gradient (density-based)

Controls:
- Ctrl+C: Exit

Inspired by: Amiga/DOS demo scene (1992-1998)
Session: Deep Work Session 3/6 (CREATIVE)
Date: 2026-03-28
"""

import math
import sys
import time
import os
from typing import Tuple


# PSX-inspired 256-color palette (blues, purples, pinks, whites)
PSX_PALETTE = [
    # Dark blues (0-15)
    16, 17, 18, 19, 20, 21, 26, 27, 32, 33, 38, 39, 44, 45, 50, 51,
    # Mid blues (16-31)
    57, 63, 69, 75, 81, 87, 93, 99, 105, 111, 117, 123, 129, 135, 141, 147,
    # Purples (32-47)
    91, 92, 93, 128, 129, 130, 164, 165, 166, 201, 202, 203, 207, 213, 219, 225,
    # Pinks (48-63)
    197, 198, 199, 205, 206, 211, 212, 217, 218, 223, 224, 229, 230, 231, 255, 255,
    # Whites/highlights (64-79)
    231, 231, 255, 255, 231, 231, 255, 255, 231, 231, 255, 255, 231, 231, 255, 255,
    # Cycle back darker
    225, 219, 213, 207, 201, 165, 129, 93, 57, 51, 45, 39, 33, 27, 21, 17,
]

# ASCII gradient (dark to light, density-based)
ASCII_GRADIENT = " .:-=+*#%@"


class PlasmaField:
    """Plasma field generator with sine wave interference"""

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.time = 0.0
        self.palette = PSX_PALETTE

    def calculate_plasma_value(self, x: int, y: int, t: float) -> float:
        """
        Calculate plasma value at (x, y) using multiple sine waves
        
        Classic plasma formula:
        P(x,y,t) = sin(x/8 + t) + sin(y/8 + t) + sin((x+y)/16 + t) + sin(sqrt(x²+y²)/8 + t)
        """
        # Normalize coordinates to [-π, π]
        nx = (x - self.width / 2) / (self.width / 4)
        ny = (y - self.height / 2) / (self.height / 4)
        
        # Four sine wave components (classic plasma)
        v1 = math.sin(nx * 0.5 + t)
        v2 = math.sin(ny * 0.5 + t)
        v3 = math.sin((nx + ny) * 0.3 + t)
        
        # Distance-based component
        dist = math.sqrt(nx * nx + ny * ny)
        v4 = math.sin(dist * 0.4 + t)
        
        # Combine waves (average)
        plasma = (v1 + v2 + v3 + v4) / 4.0
        
        # Normalize to [0, 1]
        return (plasma + 1.0) / 2.0

    def get_color_index(self, value: float) -> int:
        """Map plasma value [0,1] to palette index"""
        idx = int(value * (len(self.palette) - 1))
        return self.palette[idx]

    def get_ascii_char(self, value: float) -> str:
        """Map plasma value [0,1] to ASCII character"""
        idx = int(value * (len(ASCII_GRADIENT) - 1))
        return ASCII_GRADIENT[idx]

    def render_frame(self, use_color: bool = True) -> str:
        """Render single frame of plasma field"""
        lines = []
        
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                value = self.calculate_plasma_value(x, y, self.time)
                
                if use_color:
                    color_idx = self.get_color_index(value)
                    char = self.get_ascii_char(value)
                    # ANSI 256-color escape
                    line += f"\033[38;5;{color_idx}m{char}"
                else:
                    char = self.get_ascii_char(value)
                    line += char
            
            if use_color:
                line += "\033[0m"  # Reset color
            lines.append(line)
        
        return "\n".join(lines)

    def animate(self, duration: float = 30.0, fps: int = 30, use_color: bool = True):
        """
        Animate plasma field
        
        Args:
            duration: Total animation time (seconds)
            fps: Target frames per second
            use_color: Use 256-color ANSI codes
        """
        frame_delay = 1.0 / fps
        start_time = time.time()
        frame_count = 0
        
        try:
            # Hide cursor
            sys.stdout.write("\033[?25l")
            
            while (time.time() - start_time) < duration:
                frame_start = time.time()
                
                # Clear screen and move cursor to top-left
                sys.stdout.write("\033[2J\033[H")
                
                # Render frame
                frame = self.render_frame(use_color=use_color)
                sys.stdout.write(frame)
                
                # Stats overlay
                elapsed = time.time() - start_time
                fps_actual = frame_count / elapsed if elapsed > 0 else 0
                stats = f"\n\nPlasma Field | Frame: {frame_count} | FPS: {fps_actual:.1f} | Time: {self.time:.2f}s"
                sys.stdout.write(stats)
                
                sys.stdout.flush()
                
                # Advance time (controls animation speed)
                self.time += 0.05
                frame_count += 1
                
                # Frame rate limiting
                frame_time = time.time() - frame_start
                sleep_time = max(0, frame_delay - frame_time)
                time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            # Show cursor, reset color
            sys.stdout.write("\033[?25h\033[0m\n")
            print(f"\nRendered {frame_count} frames in {time.time() - start_time:.2f}s")


def main():
    """Main entry point"""
    # Get terminal size
    try:
        term_size = os.get_terminal_size()
        width = min(term_size.columns, 120)
        height = min(term_size.lines - 4, 40)  # Leave room for stats
    except OSError:
        width, height = 80, 24
    
    plasma = PlasmaField(width=width, height=height)
    
    print("═" * width)
    print("PLASMA FIELD GENERATOR".center(width))
    print("Classic demoscene effect (1990s)".center(width))
    print("Press Ctrl+C to exit".center(width))
    print("═" * width)
    time.sleep(2)
    
    # Detect color support
    use_color = sys.stdout.isatty() and os.getenv("TERM") != "dumb"
    
    plasma.animate(duration=60.0, fps=30, use_color=use_color)


if __name__ == "__main__":
    main()
