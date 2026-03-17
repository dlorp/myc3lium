#!/usr/bin/env python3
"""
IBM VGA 8×16 Font Atlas Generator (Python)

Generates a 128×128px PNG atlas containing all 256 characters
from the IBM VGA Code Page 437 charset.

Requires: pillow (pip install pillow)
Usage: python3 generate-font-atlas.py
"""

from PIL import Image, ImageDraw, ImageFont
import json
import os

# IBM VGA CP437 full character map (256 chars)
CP437_CHARS = [
    # 0x00-0x1F: Control characters (rendered as symbols in VGA)
    '\u0000', '☺', '☻', '♥', '♦', '♣', '♠', '•', '◘', '○', '◙', '♂', '♀', '♪', '♫', '☼',
    '►', '◄', '↕', '‼', '¶', '§', '▬', '↨', '↑', '↓', '→', '←', '∟', '↔', '▲', '▼',
    
    # 0x20-0x7F: Standard ASCII
    ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
    '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',
    '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', '⌂',
    
    # 0x80-0xFF: Extended ASCII / box drawing / international
    'Ç', 'ü', 'é', 'â', 'ä', 'à', 'å', 'ç', 'ê', 'ë', 'è', 'ï', 'î', 'ì', 'Ä', 'Å',
    'É', 'æ', 'Æ', 'ô', 'ö', 'ò', 'û', 'ù', 'ÿ', 'Ö', 'Ü', '¢', '£', '¥', '₧', 'ƒ',
    'á', 'í', 'ó', 'ú', 'ñ', 'Ñ', 'ª', 'º', '¿', '⌐', '¬', '½', '¼', '¡', '«', '»',
    '░', '▒', '▓', '│', '┤', '╡', '╢', '╖', '╕', '╣', '║', '╗', '╝', '╜', '╛', '┐',
    '└', '┴', '┬', '├', '─', '┼', '╞', '╟', '╚', '╔', '╩', '╦', '╠', '═', '╬', '╧',
    '╨', '╤', '╥', '╙', '╘', '╒', '╓', '╫', '╪', '┘', '┌', '█', '▄', '▌', '▐', '▀',
    'α', 'ß', 'Γ', 'π', 'Σ', 'σ', 'µ', 'τ', 'Φ', 'Θ', 'Ω', 'δ', '∞', 'φ', 'ε', '∩',
    '≡', '±', '≥', '≤', '⌠', '⌡', '÷', '≈', '°', '∙', '·', '√', 'ⁿ', '²', '■', '\u00A0'
]

CHAR_WIDTH = 8
CHAR_HEIGHT = 16
GRID_SIZE = 16  # 16×16 grid
ATLAS_SIZE = GRID_SIZE * CHAR_WIDTH  # 128px

print('Generating IBM VGA 8×16 font atlas...')
print(f'Grid: {GRID_SIZE}×{GRID_SIZE} characters')
print(f'Cell: {CHAR_WIDTH}×{CHAR_HEIGHT}px')
print(f'Atlas: {ATLAS_SIZE}×{ATLAS_SIZE}px\n')

# Create image
img = Image.new('RGBA', (ATLAS_SIZE, ATLAS_SIZE), color=(0, 0, 0, 255))
draw = ImageDraw.Draw(img)

# Try to use a monospace font
try:
    # Try common monospace fonts
    font_options = [
        '/System/Library/Fonts/Courier.dfont',  # macOS
        '/Library/Fonts/Courier New.ttf',
        'C:\\Windows\\Fonts\\cour.ttf',  # Windows
        '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',  # Linux
    ]
    
    font = None
    for font_path in font_options:
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 14)
            print(f'Using font: {font_path}')
            break
    
    if font is None:
        print('Using default font (PIL ImageFont)')
        font = ImageFont.load_default()
except Exception as e:
    print(f'Font loading error: {e}')
    font = ImageFont.load_default()

# Render each character
for i in range(256):
    char = CP437_CHARS[i]
    col = i % GRID_SIZE
    row = i // GRID_SIZE
    
    x = col * CHAR_WIDTH
    y = row * CHAR_HEIGHT
    
    # Draw character (white on black)
    try:
        draw.text((x + 1, y), char, fill=(255, 255, 255, 255), font=font)
    except Exception as e:
        # Some characters might not render in all fonts
        pass

# Save PNG
out_path = 'ibm-vga-8x16.png'
img.save(out_path, 'PNG')
file_size = os.path.getsize(out_path)

print(f'\n✓ Font atlas generated: {out_path}')
print(f'  Size: {file_size} bytes')
print(f'  Dimensions: {ATLAS_SIZE}×{ATLAS_SIZE}px')
print(f'  Characters: 256 (CP437 charset)\n')

# Generate metadata JSON
metadata = {
    'version': '1.0.0',
    'charset': 'IBM VGA Code Page 437',
    'charWidth': CHAR_WIDTH,
    'charHeight': CHAR_HEIGHT,
    'gridSize': GRID_SIZE,
    'atlasWidth': ATLAS_SIZE,
    'atlasHeight': ATLAS_SIZE,
    'totalChars': 256,
    'usage': {
        'texCoordU': 'charIndex % 16 * 8 / 128',
        'texCoordV': 'Math.floor(charIndex / 16) * 16 / 128'
    }
}

meta_path = 'ibm-vga-8x16.json'
with open(meta_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f'✓ Metadata generated: {meta_path}\n')
print('Atlas generation complete.')
