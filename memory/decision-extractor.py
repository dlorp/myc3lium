#!/usr/bin/env python3
"""
OpenClaw Decision Extractor
Parses #session-notes for decision markers, auto-adds to MEMORY.md.
"""

import re
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
DECISIONS_FILE = MEMORY_DIR / "extracted-decisions.json"

# NLP decision markers
DECISION_PATTERNS = [
    r'decided to (.+)',
    r'decision: (.+)',
    r'chose (.+)',
    r'picked (.+)',
    r'went with (.+)',
    r'settled on (.+)',
    r'committed to (.+)',
    r'agreed to (.+)'
]

def extract_decisions(text):
    """Extract decisions from text using NLP markers."""
    decisions = []
    
    for pattern in DECISION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get context (surrounding lines)
            pos = match.start()
            lines = text[:pos].split('\n')
            
            decision = {
                'text': match.group(1).strip(),
                'marker': match.group(0),
                'context': lines[-1] if lines else "",
                'confidence': 0.8  # High confidence for explicit markers
            }
            decisions.append(decision)
    
    return decisions

def parse_session_notes(content):
    """Parse session notes format for decisions."""
    decisions = []
    
    # Look for decision-like headers
    sections = re.split(r'\n##+ ', content)
    
    for section in sections:
        lines = section.split('\n')
        header = lines[0] if lines else ""
        body = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        
        # Extract from each section
        section_decisions = extract_decisions(body)
        
        for decision in section_decisions:
            decision['section'] = header.strip()
            decisions.append(decision)
    
    return decisions

def load_extracted_decisions():
    """Load previously extracted decisions."""
    if DECISIONS_FILE.exists():
        with open(DECISIONS_FILE) as f:
            return json.load(f)
    return []

def save_extracted_decisions(decisions):
    """Save extracted decisions."""
    with open(DECISIONS_FILE, 'w') as f:
        json.dump(decisions, f, indent=2)

def format_decision_for_memory(decision, date):
    """Format decision for MEMORY.md Key Decisions section."""
    return f"**{date}:** {decision['text']}"

def suggest_memory_update(decisions, source_date):
    """Generate suggested MEMORY.md update."""
    if not decisions:
        return None
    
    suggestion = f"\n## Suggested Key Decisions (from {source_date})\n\n"
    
    for decision in decisions:
        suggestion += f"**{source_date}:** {decision['text']}\n"
        if decision.get('section'):
            suggestion += f"  _(Context: {decision['section']})_\n"
        suggestion += "\n"
    
    return suggestion

def main():
    """Extract decisions from session notes."""
    print("OpenClaw Decision Extractor")
    print("=" * 70)
    
    # Example: parse today's session notes
    # TODO: Integrate with Discord message tool to read #session-notes
    # For now, use example text
    
    example_session_note = """
## Deep Work Session 3 — t3rra1n BBox & Lorp Analysis
**Date:** 2026-02-14 | **Time:** 00:41-00:53 AKST

### Key Decisions

**Decided to implement multi-equipment interaction** as Phase 1 priority.
This will increase lore depth by 2 points.

**Chose to use PIL + tkinter** for bbox editor instead of web-based UI.
Went with external window approach for pixel-accurate editing.

**Settled on 5 color-coded overlays** for multi-bbox support.
    """
    
    print("\nParsing session notes...")
    decisions = parse_session_notes(example_session_note)
    
    print(f"  Found {len(decisions)} decisions")
    for i, decision in enumerate(decisions, 1):
        print(f"  {i}. {decision['text']}")
        print(f"     Confidence: {decision['confidence']:.0%}")
        print(f"     Context: {decision.get('section', 'N/A')}")
        print()
    
    # Generate suggestion
    if decisions:
        suggestion = suggest_memory_update(decisions, "2026-02-14")
        print("\n" + "=" * 70)
        print("SUGGESTED MEMORY.md UPDATE")
        print("=" * 70)
        print(suggestion)
        
        # Save for review
        all_decisions = load_extracted_decisions()
        for decision in decisions:
            decision['extractedAt'] = datetime.now().isoformat()
            decision['status'] = 'pending_review'
            all_decisions.append(decision)
        save_extracted_decisions(all_decisions)
        
        print(f"\n✓ Saved {len(decisions)} decisions to {DECISIONS_FILE}")
        print("  Review and integrate during next heartbeat")

if __name__ == '__main__':
    main()
