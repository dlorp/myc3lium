#!/usr/bin/env python3
"""
tunnel-effect.py — Classic 3D tunnel demoscene effect (ASCII)

Generates real-time 3D tunnel visualization using polar coordinates
and texture mapping. Classic demoscene technique from 1990s.

Features:
- Polar coordinate transformation (3D tunnel projection)
- Animated texture scrolling
- 256-color palette (PSX aesthetic)
- Depth-based fog/shading
- ASCII character gradient

Controls:
- Ctrl+C: Exit

Inspired by: Second Reality (Future Crew, 1993)
Session: Deep Work Session 3/6 (CREATIVE)
Date: 2026-03-28
"""

import math
import sys
import time
import os
from typing import Tuple


# PSX-inspired 256-color palette (blues -> cyans -> whites)
PSX_TUNNEL_PALETTE = [
    # Deep blues (far/dark)
    16, 17, 18, 19, 20, 21,
    # Mid blues
    26, 27, 32, 33, 38, 39,
    # Bright blues -> cyans
    44, 45, 50, 51, 73, 74, 79, 80, 85, 86,
    # Cyans -> whites (near/bright)
    123, 159, 195, 231, 255,
]

# ASCII gradient (depth-based, dark to light)
ASCII_TUNNEL_GRADIENT = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


class TunnelEffect:
    """3D tunnel effect generator using polar coordinates"""

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.time = 0.0
        self.palette = PSX_TUNNEL_PALETTE
        
        # Pre-calculate polar coordinate lookup tables (optimization)
        self.distance_table = []
        self.angle_table = []
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Pre-calculate distance and angle for each screen coordinate"""
        center_x = self.width / 2
        center_y = self.height / 2
        
        for y in range(self.height):
            dist_row = []
            angle_row = []
            
            for x in range(self.width):
                # Convert to centered coordinates
                dx = x - center_x
                dy = (y - center_y) * 2  # 2x to compensate for character aspect ratio
                
                # Polar coordinates
                distance = math.sqrt(dx * dx + dy * dy)
                angle = math.atan2(dy, dx)
                
                dist_row.append(distance)
                angle_row.append(angle)
            
            self.distance_table.append(dist_row)
            self.angle_table.append(angle_row)

    def calculate_tunnel_value(self, x: int, y: int, t: float) -> Tuple[float, float]:
        """
        Calculate tunnel texture coordinates at screen position (x, y)
        
        Returns:
            (depth, intensity): depth = distance into tunnel, intensity = brightness
        """
        distance = self.distance_table[y][x]
        angle = self.angle_table[y][x]
        
        # Prevent division by zero (center point)
        if distance < 0.1:
            distance = 0.1
        
        # Tunnel depth (1/distance creates perspective)
        depth = 32.0 / distance + t
        
        # Tunnel angle (rotation animation)
        u = angle * 4.0 / math.pi
        
        # Texture coordinates (scrolling checkerboard)
        texture_u = int(u + t * 2) % 2
        texture_v = int(depth) % 2
        
        # Checkerboard pattern
        pattern = (texture_u + texture_v) % 2
        
        # Depth-based intensity (fog effect)
        intensity = 1.0 / (1.0 + distance / 20.0)
        intensity = max(0.0, min(1.0, intensity))
        
        # Modulate intensity by pattern
        if pattern == 0:
            intensity *= 0.5
        
        return depth, intensity

    def get_color_index(self, intensity: float) -> int:
        """Map intensity [0,1] to palette index"""
        idx = int(intensity * (len(self.palette) - 1))
        return self.palette[idx]

    def get_ascii_char(self, intensity: float) -> str:
        """Map intensity [0,1] to ASCII character"""
        idx = int(intensity * (len(ASCII_TUNNEL_GRADIENT) - 1))
        return ASCII_TUNNEL_GRADIENT[idx]

    def render_frame(self, use_color: bool = True) -> str:
        """Render single frame of tunnel effect"""
        lines = []
        
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                depth, intensity = self.calculate_tunnel_value(x, y, self.time)
                
                if use_color:
                    color_idx = self.get_color_index(intensity)
                    char = self.get_ascii_char(intensity)
                    # ANSI 256-color escape
                    line += f"\033[38;5;{color_idx}m{char}"
                else:
                    char = self.get_ascii_char(intensity)
                    line += char
            
            if use_color:
                line += "\033[0m"  # Reset color
            lines.append(line)
        
        return "\n".join(lines)

    def animate(self, duration: float = 30.0, fps: int = 30, use_color: bool = True):
        """
        Animate tunnel effect
        
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
                stats = f"\n\n3D TUNNEL | Frame: {frame_count} | FPS: {fps_actual:.1f} | Depth: {self.time:.2f}"
                sys.stdout.write(stats)
                
                sys.stdout.flush()
                
                # Advance time (controls scroll speed)
                self.time += 0.08
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
    
    tunnel = TunnelEffect(width=width, height=height)
    
    print("═" * width)
    print("3D TUNNEL EFFECT".center(width))
    print("Classic demoscene technique (Future Crew, 1993)".center(width))
    print("Press Ctrl+C to exit".center(width))
    print("═" * width)
    time.sleep(2)
    
    # Detect color support
    use_color = sys.stdout.isatty() and os.getenv("TERM") != "dumb"
    
    tunnel.animate(duration=60.0, fps=30, use_color=use_color)


if __name__ == "__main__":
    main()
