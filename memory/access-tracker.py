#!/usr/bin/env python3
"""
OpenClaw Memory Access Tracker
Logs which sections of MEMORY.md get accessed most often.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORY_DIR = Path(__file__).parent
ACCESS_LOG = MEMORY_DIR / "access-log.jsonl"
ACCESS_STATS = MEMORY_DIR / "access-stats.json"

def log_access(section, context=""):
    """Log a memory access event."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "section": section,
        "context": context
    }
    
    with open(ACCESS_LOG, 'a') as f:
        f.write(json.dumps(event) + '\n')

def generate_stats():
    """Generate access statistics from log."""
    if not ACCESS_LOG.exists():
        print("No access log found.")
        return
    
    stats = defaultdict(lambda: {"count": 0, "lastAccessed": None})
    
    with open(ACCESS_LOG) as f:
        for line in f:
            if not line.strip():
                continue
            event = json.loads(line)
            section = event['section']
            stats[section]['count'] += 1
            stats[section]['lastAccessed'] = event['timestamp']
    
    # Convert to regular dict and sort by count
    stats_dict = dict(stats)
    sorted_sections = sorted(stats_dict.items(), key=lambda x: x[1]['count'], reverse=True)
    
    # Save stats
    output = {
        "generatedAt": datetime.now().isoformat(),
        "totalAccesses": sum(s['count'] for s in stats_dict.values()),
        "uniqueSections": len(stats_dict),
        "sections": {k: v for k, v in sorted_sections}
    }
    
    with open(ACCESS_STATS, 'w') as f:
        json.dump(output, f, indent=2)
    
    return output

def print_stats(stats):
    """Print access statistics."""
    print("\nMemory Access Statistics")
    print("=" * 70)
    print(f"Total accesses: {stats['totalAccesses']}")
    print(f"Unique sections: {stats['uniqueSections']}")
    print(f"Generated: {stats['generatedAt']}")
    
    print("\nTop 10 Most Accessed Sections:")
    print("-" * 70)
    
    for i, (section, data) in enumerate(list(stats['sections'].items())[:10], 1):
        print(f"{i}. {section}")
        print(f"   Accesses: {data['count']}")
        print(f"   Last accessed: {data['lastAccessed']}")
        print()
    
    # Find dead weight (never or rarely accessed)
    rarely_accessed = [(k, v) for k, v in stats['sections'].items() if v['count'] <= 2]
    if rarely_accessed:
        print(f"\nRarely Accessed ({len(rarely_accessed)} sections with ≤2 accesses):")
        print("-" * 70)
        for section, data in rarely_accessed[:5]:
            print(f"  • {section} ({data['count']} accesses)")

def main():
    """Generate and display access statistics."""
    stats = generate_stats()
    if stats:
        print_stats(stats)
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if stats and stats['sections']:
        top_section = list(stats['sections'].items())[0]
        print(f"\n✓ Most valuable: {top_section[0]}")
        print(f"  → Keep this easily accessible")
        
        rarely = [(k, v) for k, v in stats['sections'].items() if v['count'] <= 2]
        if len(rarely) > 5:
            print(f"\n⚠ {len(rarely)} sections rarely accessed")
            print("  → Consider archiving or restructuring")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'log':
        if len(sys.argv) < 3:
            print("Usage: access-tracker.py log <section> [context]")
            sys.exit(1)
        section = sys.argv[2]
        context = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        log_access(section, context)
        print(f"✓ Logged access to: {section}")
    else:
        main()
