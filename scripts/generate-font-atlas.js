#!/usr/bin/env node
/**
 * IBM VGA 8×16 Font Atlas Generator
 * 
 * Generates a 128×128px PNG atlas containing all 256 characters
 * from the IBM VGA Code Page 437 charset (retro terminal aesthetic).
 * 
 * Grid: 16×16 characters (256 total)
 * Cell: 8×16 pixels per character
 * Output: ibm-vga-8x16.png (128×128px)
 * 
 * Usage: node generate-font-atlas.js
 */

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

// IBM VGA CP437 full character map (256 chars)
// This represents the iconic IBM PC character set
const CP437_CHARS = [
  // 0x00-0x1F: Control characters (rendered as symbols in VGA)
  '\u0000', '☺', '☻', '♥', '♦', '♣', '♠', '•', '◘', '○', '◙', '♂', '♀', '♪', '♫', '☼',
  '►', '◄', '↕', '‼', '¶', '§', '▬', '↨', '↑', '↓', '→', '←', '∟', '↔', '▲', '▼',
  
  // 0x20-0x7F: Standard ASCII
  ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/',
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
  '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
  'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',
  '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
  'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', '⌂',
  
  // 0x80-0xFF: Extended ASCII / box drawing / international
  'Ç', 'ü', 'é', 'â', 'ä', 'à', 'å', 'ç', 'ê', 'ë', 'è', 'ï', 'î', 'ì', 'Ä', 'Å',
  'É', 'æ', 'Æ', 'ô', 'ö', 'ò', 'û', 'ù', 'ÿ', 'Ö', 'Ü', '¢', '£', '¥', '₧', 'ƒ',
  'á', 'í', 'ó', 'ú', 'ñ', 'Ñ', 'ª', 'º', '¿', '⌐', '¬', '½', '¼', '¡', '«', '»',
  '░', '▒', '▓', '│', '┤', '╡', '╢', '╖', '╕', '╣', '║', '╗', '╝', '╜', '╛', '┐',
  '└', '┴', '┬', '├', '─', '┼', '╞', '╟', '╚', '╔', '╩', '╦', '╠', '═', '╬', '╧',
  '╨', '╤', '╥', '╙', '╘', '╒', '╓', '╫', '╪', '┘', '┌', '█', '▄', '▌', '▐', '▀',
  'α', 'ß', 'Γ', 'π', 'Σ', 'σ', 'µ', 'τ', 'Φ', 'Θ', 'Ω', 'δ', '∞', 'φ', 'ε', '∩',
  '≡', '±', '≥', '≤', '⌠', '⌡', '÷', '≈', '°', '∙', '·', '√', 'ⁿ', '²', '■', '\u00A0'
];

const CHAR_WIDTH = 8;
const CHAR_HEIGHT = 16;
const GRID_SIZE = 16; // 16×16 grid
const ATLAS_SIZE = GRID_SIZE * CHAR_WIDTH; // 128px

console.log('Generating IBM VGA 8×16 font atlas...');
console.log(`Grid: ${GRID_SIZE}×${GRID_SIZE} characters`);
console.log(`Cell: ${CHAR_WIDTH}×${CHAR_HEIGHT}px`);
console.log(`Atlas: ${ATLAS_SIZE}×${ATLAS_SIZE}px\n`);

// Create canvas
const canvas = createCanvas(ATLAS_SIZE, ATLAS_SIZE);
const ctx = canvas.getContext('2d');

// Background: black
ctx.fillStyle = '#000000';
ctx.fillRect(0, 0, ATLAS_SIZE, ATLAS_SIZE);

// Font rendering settings
ctx.fillStyle = '#FFFFFF'; // White text
ctx.font = `${CHAR_HEIGHT}px "Courier New", monospace`;
ctx.textBaseline = 'top';
ctx.textAlign = 'left';

// Render each character
for (let i = 0; i < 256; i++) {
  const char = CP437_CHARS[i];
  const col = i % GRID_SIZE;
  const row = Math.floor(i / GRID_SIZE);
  
  const x = col * CHAR_WIDTH;
  const y = row * CHAR_HEIGHT;
  
  // Draw character (centered in 8px width)
  // Note: Canvas text rendering won't perfectly match IBM VGA bitmap,
  // but provides a functional approximation for prototyping
  ctx.fillText(char, x, y);
}

// Save PNG
const outPath = path.join(__dirname, 'ibm-vga-8x16.png');
const buffer = canvas.toBuffer('image/png');
fs.writeFileSync(outPath, buffer);

console.log(`✓ Font atlas generated: ${outPath}`);
console.log(`  Size: ${buffer.length} bytes`);
console.log(`  Dimensions: ${ATLAS_SIZE}×${ATLAS_SIZE}px`);
console.log(`  Characters: 256 (CP437 charset)\n`);

// Generate metadata JSON
const metadata = {
  version: '1.0.0',
  charset: 'IBM VGA Code Page 437',
  charWidth: CHAR_WIDTH,
  charHeight: CHAR_HEIGHT,
  gridSize: GRID_SIZE,
  atlasWidth: ATLAS_SIZE,
  atlasHeight: ATLAS_SIZE,
  totalChars: 256,
  usage: {
    texCoordU: 'charIndex % 16 * 8 / 128',
    texCoordV: 'Math.floor(charIndex / 16) * 16 / 128'
  }
};

const metaPath = path.join(__dirname, 'ibm-vga-8x16.json');
fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2));

console.log(`✓ Metadata generated: ${metaPath}\n`);
console.log('Atlas generation complete.');
