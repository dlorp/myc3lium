#!/usr/bin/env python3
"""
OpenClaw Memory Indexer
Creates and maintains SQLite FTS5 index of MEMORY.md and daily logs.
"""

import sqlite3
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"
DB_PATH = MEMORY_DIR / "memory.db"

def get_file_hash(path):
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse_memory_md(content):
    """Parse MEMORY.md into sections."""
    sections = []
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        # Match headers (## Active Axioms, ## Key Decisions, etc.)
        if line.startswith('## '):
            if current_section:
                sections.append({
                    'section': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Add final section
    if current_section:
        sections.append({
            'section': current_section,
            'content': '\n'.join(current_content).strip()
        })
    
    return sections

def extract_axioms(content):
    """Extract axioms from MEMORY.md for structured table."""
    axioms = []
    
    # Pattern: **[AXIOM-XXX]** Title
    pattern = r'\*\*\[AXIOM-(\d+)\]\*\*\s+(.+?)(?:\n|$)'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        number = int(match.group(1))
        title = match.group(2).strip()
        
        # Try to extract the rule (next line starting with >)
        pos = match.end()
        rule_match = re.search(r'>\s*(.+)', content[pos:pos+200])
        rule = rule_match.group(1) if rule_match else ""
        
        axioms.append({
            'id': f'AXIOM-{number:03d}',
            'number': number,
            'title': title,
            'rule': rule
        })
    
    return axioms

def index_file(conn, file_path, category='unknown'):
    """Index a single file into FTS."""
    cursor = conn.cursor()
    
    # Check if file changed since last index
    file_hash = get_file_hash(file_path)
    cursor.execute(
        "SELECT file_hash FROM memory_index_meta WHERE file_path = ?",
        (str(file_path),)
    )
    row = cursor.fetchone()
    if row and row[0] == file_hash:
        print(f"  Skipped (unchanged): {file_path.name}")
        return
    
    # Delete old entries for this file
    cursor.execute(
        "DELETE FROM memory_fts WHERE source = ?",
        (str(file_path.relative_to(WORKSPACE)),)
    )
    
    # Parse and index content
    content = file_path.read_text()
    source = str(file_path.relative_to(WORKSPACE))
    timestamp = datetime.now().isoformat()
    
    if file_path.name == 'MEMORY.md':
        sections = parse_memory_md(content)
        for sec in sections:
            cursor.execute(
                "INSERT INTO memory_fts(source, section, content, timestamp, category) VALUES (?, ?, ?, ?, ?)",
                (source, sec['section'], sec['content'], timestamp, category)
            )
        
        # Extract and insert axioms into structured table
        axioms = extract_axioms(content)
        for axiom in axioms:
            cursor.execute(
                "INSERT OR REPLACE INTO axioms(id, number, title, rule) VALUES (?, ?, ?, ?)",
                (axiom['id'], axiom['number'], axiom['title'], axiom['rule'])
            )
    else:
        # Daily log - index as single entry
        cursor.execute(
            "INSERT INTO memory_fts(source, section, content, timestamp, category) VALUES (?, ?, ?, ?, ?)",
            (source, file_path.stem, content, timestamp, category)
        )
    
    # Update metadata
    cursor.execute(
        "SELECT COUNT(*) FROM memory_fts WHERE source = ?",
        (source,)
    )
    entry_count = cursor.fetchone()[0]
    
    cursor.execute(
        "INSERT OR REPLACE INTO memory_index_meta(file_path, last_indexed, file_hash, entry_count) VALUES (?, ?, ?, ?)",
        (source, int(datetime.now().timestamp()), file_hash, entry_count)
    )
    
    print(f"  Indexed: {file_path.name} ({entry_count} entries)")

def main():
    """Index all memory files."""
    print("OpenClaw Memory Indexer")
    print("=" * 50)
    
    # Initialize database
    conn = sqlite3.connect(DB_PATH)
    with open(MEMORY_DIR / 'setup-fts.sql') as f:
        conn.executescript(f.read())
    print("✓ Database initialized")
    
    # Index MEMORY.md
    print("\nIndexing MEMORY.md...")
    memory_md = WORKSPACE / 'MEMORY.md'
    if memory_md.exists():
        index_file(conn, memory_md, category='memory')
    
    # Index daily logs
    print("\nIndexing daily logs...")
    daily_logs = sorted(MEMORY_DIR.glob('20*.md'))
    for log_file in daily_logs:
        index_file(conn, log_file, category='daily')
    
    conn.commit()
    
    # Print stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM memory_fts")
    total_entries = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM axioms")
    total_axioms = cursor.fetchone()[0]
    
    print("\n" + "=" * 50)
    print(f"✓ Indexing complete")
    print(f"  Total FTS entries: {total_entries}")
    print(f"  Total axioms: {total_axioms}")
    print(f"  Database: {DB_PATH}")
    
    conn.close()

if __name__ == '__main__':
    main()
