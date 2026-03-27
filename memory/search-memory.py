#!/usr/bin/env python3
"""
OpenClaw Memory Search
Query the FTS5 index for fast semantic search across all memory.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "memory.db"

def search_memory(query, limit=10):
    """Search memory using FTS5."""
    if not DB_PATH.exists():
        print("Error: Memory database not found. Run index-memory.py first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # FTS5 query with ranking
    cursor.execute("""
        SELECT 
            source,
            section,
            snippet(memory_fts, 2, '<mark>', '</mark>', '...', 32) as snippet,
            rank
        FROM memory_fts
        WHERE memory_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"No results found for: {query}")
        return
    
    print(f"\nFound {len(results)} result(s) for: {query}")
    print("=" * 70)
    
    for i, (source, section, snippet, rank) in enumerate(results, 1):
        print(f"\n{i}. {source} → {section}")
        print(f"   {snippet}")
        print(f"   (relevance: {-rank:.2f})")
    
    print()

def search_axioms(query=None, category=None):
    """Search axioms table with optional filters."""
    if not DB_PATH.exists():
        print("Error: Memory database not found. Run index-memory.py first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if query:
        # Full-text search in axioms
        cursor.execute("""
            SELECT id, title, rule, category
            FROM axioms
            WHERE title LIKE ? OR rule LIKE ?
            ORDER BY number
        """, (f'%{query}%', f'%{query}%'))
    elif category:
        cursor.execute("""
            SELECT id, title, rule, category
            FROM axioms
            WHERE category = ?
            ORDER BY number
        """, (category,))
    else:
        cursor.execute("""
            SELECT id, title, rule, category
            FROM axioms
            WHERE status = 'active'
            ORDER BY number
        """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"No axioms found.")
        return
    
    print(f"\nFound {len(results)} axiom(s)")
    print("=" * 70)
    
    for axiom_id, title, rule, cat in results:
        print(f"\n{axiom_id}: {title}")
        if rule:
            print(f"  > {rule}")
        print(f"  Category: {cat or 'unknown'}")
    
    print()

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  search-memory.py <query>              # Search all memory")
        print("  search-memory.py --axioms [query]     # Search axioms")
        print("  search-memory.py --axioms -c workflow # List axioms by category")
        print()
        print("Examples:")
        print("  search-memory.py 'exec approval'")
        print("  search-memory.py --axioms git")
        print("  search-memory.py --axioms -c workflow")
        sys.exit(1)
    
    if sys.argv[1] == '--axioms':
        if len(sys.argv) > 2:
            if sys.argv[2] == '-c' and len(sys.argv) > 3:
                search_axioms(category=sys.argv[3])
            else:
                search_axioms(query=' '.join(sys.argv[2:]))
        else:
            search_axioms()
    else:
        query = ' '.join(sys.argv[1:])
        search_memory(query)

if __name__ == '__main__':
    main()
