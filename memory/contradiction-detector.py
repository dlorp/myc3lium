#!/usr/bin/env python3
"""
OpenClaw Contradiction Detector
Flags when new patterns conflict with existing axioms.
"""

import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
MEMORY_FILE = WORKSPACE / "MEMORY.md"

# Simple contradiction patterns (keyword-based)
CONTRADICTION_KEYWORDS = {
    "always": ["never", "don't", "avoid", "skip"],
    "never": ["always", "must", "should"],
    "prefer": ["avoid", "don't use"],
    "use": ["avoid", "don't use", "never use"],
    "required": ["optional", "not needed"],
    "mandatory": ["optional", "skip"]
}

class ContradictionDetector:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.axioms = self._load_axioms()
    
    def _load_axioms(self):
        """Load existing axioms from MEMORY.md."""
        if not self.memory_file.exists():
            return []
        
        content = self.memory_file.read_text()
        axioms = []
        
        # Extract axioms (format: **[AXIOM-XXX]** Title)
        pattern = r'\*\*\[AXIOM-(\d+)\]\*\*\s+(.+?)(?:\n|$)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            number = int(match.group(1))
            title = match.group(2).strip()
            
            # Try to extract rule (next line with >)
            pos = match.end()
            rule_match = re.search(r'>\s*(.+)', content[pos:pos+300])
            rule = rule_match.group(1) if rule_match else ""
            
            axioms.append({
                'id': f'AXIOM-{number:03d}',
                'number': number,
                'title': title,
                'rule': rule,
                'text': f"{title} {rule}".lower()
            })
        
        return axioms
    
    def _find_keyword_contradictions(self, new_pattern):
        """Find contradictions using keyword matching."""
        contradictions = []
        new_text = new_pattern.lower()
        
        for axiom in self.axioms:
            axiom_text = axiom['text']
            
            # Check each keyword pair
            for keyword, opposites in CONTRADICTION_KEYWORDS.items():
                # If new pattern has keyword and axiom has opposite
                if keyword in new_text:
                    for opposite in opposites:
                        if opposite in axiom_text:
                            contradictions.append({
                                'axiom': axiom['id'],
                                'axiom_text': axiom['title'],
                                'new_pattern': new_pattern,
                                'reason': f"New pattern uses '{keyword}' but axiom uses '{opposite}'",
                                'confidence': 0.6
                            })
        
        return contradictions
    
    def _find_semantic_contradictions(self, new_pattern):
        """
        Find contradictions using semantic similarity.
        Requires sentence-transformers (optional).
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
        except ImportError:
            return []
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Embed new pattern
        new_emb = model.encode([new_pattern])[0]
        
        # Embed axioms
        axiom_texts = [a['text'] for a in self.axioms]
        axiom_embs = model.encode(axiom_texts)
        
        # Find high similarity (>0.8) with opposite sentiment
        contradictions = []
        for i, axiom in enumerate(self.axioms):
            similarity = cosine_similarity([new_emb], [axiom_embs[i]])[0][0]
            
            # High similarity but opposite meaning (contains not/never/avoid)
            if similarity > 0.7:
                new_has_negative = any(word in new_pattern.lower() for word in ["not", "never", "avoid", "don't"])
                axiom_has_negative = any(word in axiom['text'] for word in ["not", "never", "avoid", "don't"])
                
                if new_has_negative != axiom_has_negative:
                    contradictions.append({
                        'axiom': axiom['id'],
                        'axiom_text': axiom['title'],
                        'new_pattern': new_pattern,
                        'reason': f"Similar topic but opposite stance (similarity: {similarity:.0%})",
                        'confidence': 0.8
                    })
        
        return contradictions
    
    def detect(self, new_pattern: str):
        """Detect contradictions with existing axioms."""
        print(f"\nChecking pattern: {new_pattern}")
        print("=" * 70)
        
        # Keyword-based
        keyword_contradictions = self._find_keyword_contradictions(new_pattern)
        
        # Semantic (optional) - disabled due to dependency issues
        semantic_contradictions = []
        # try:
        #     semantic_contradictions = self._find_semantic_contradictions(new_pattern)
        # except:
        #     semantic_contradictions = []
        
        all_contradictions = keyword_contradictions + semantic_contradictions
        
        if not all_contradictions:
            print("✓ No contradictions detected")
            return []
        
        print(f"⚠️  Found {len(all_contradictions)} potential contradiction(s):")
        for c in all_contradictions:
            print(f"\n  Conflicts with: {c['axiom']}")
            print(f"  Existing axiom: {c['axiom_text']}")
            print(f"  Reason: {c['reason']}")
            print(f"  Confidence: {c['confidence']:.0%}")
        
        return all_contradictions

# CLI
if __name__ == '__main__':
    import sys
    
    detector = ContradictionDetector()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  contradiction-detector.py \"<pattern>\"")
        print("\nExamples:")
        print("  contradiction-detector.py \"Always use rm for fast deletion\"")
        print("  contradiction-detector.py \"Never wait for CI before merging\"")
        sys.exit(1)
    
    pattern = ' '.join(sys.argv[1:])
    contradictions = detector.detect(pattern)
    
    if contradictions:
        print("\n" + "=" * 70)
        print("RECOMMENDATION")
        print("=" * 70)
        print("\nOptions:")
        print("  1. Revise new pattern to align with existing axiom")
        print("  2. Update existing axiom if new learning invalidates it")
        print("  3. Add context to clarify when each applies")
