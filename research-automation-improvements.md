# Automation Improvements for Memory Maintenance and Knowledge Synthesis

**Generated:** 2026-03-20  
**Context:** Research on automating pattern detection, knowledge extraction, and memory updates for AI agent systems

---

## Executive Summary

This document outlines automation patterns for evolving from manual heartbeat-driven memory updates to intelligent, automated knowledge synthesis. The goal is to reduce manual overhead while improving the quality and timeliness of memory updates.

---

## 1. Automated Pattern Detection from Logs

### Current State
- Manual review during heartbeats
- Extract from specific Discord channels (#patterns, #session-notes, #axioms)
- 3+ observations → axiom candidate (manual threshold)

### Automation Approaches

#### A. Frequency-Based Pattern Mining
**Technique:** TF-IDF + N-gram Analysis
```
1. Tokenize chat logs into n-grams (unigrams, bigrams, trigrams)
2. Calculate TF-IDF scores to identify significant phrases
3. Track phrase frequency across sessions
4. Flag phrases appearing in 3+ distinct sessions/contexts
```

**Implementation:**
- Run weekly batch jobs on accumulated logs
- Use libraries: `sklearn.feature_extraction.text.TfidfVectorizer`
- Store results in `patterns-detected.json` with confidence scores

**Pros:** Simple, interpretable, good for explicit repeated phrases  
**Cons:** Misses semantic similarity, struggles with paraphrasing

#### B. Semantic Clustering
**Technique:** Embedding-based similarity detection
```
1. Generate embeddings for each chat message/session note
2. Cluster similar messages using DBSCAN or hierarchical clustering
3. Identify clusters with 3+ members as pattern candidates
4. Extract representative text from cluster centroids
```

**Implementation:**
- Use small local embeddings (all-MiniLM-L6-v2, 384 dimensions)
- Cosine similarity threshold: 0.75-0.85 for "same pattern"
- Store embeddings in vector DB (ChromaDB, FAISS) for incremental updates

**Pros:** Catches semantic similarity, handles paraphrasing  
**Cons:** More complex, requires embedding model

#### C. Hybrid Approach (Recommended)
**Combine both methods:**
1. Semantic clustering for initial grouping
2. TF-IDF within clusters to extract key phrases
3. Human review for final axiom formulation

**Threshold Logic:**
- 3+ observations in same cluster (semantic similarity > 0.8)
- OR 5+ exact phrase matches
- AND spans 2+ days/sessions (prevents single-session spam)

---

## 2. NLP Techniques for Extracting Key Decisions

### Decision Indicators

**Linguistic Patterns:**
```
Decision markers:
- "I/we decided to..."
- "Going forward, we'll..."
- "The approach is..."
- "Let's stick with..."
- "Changed my mind about..."
- "New rule: ..."
- Imperatives: "Always...", "Never...", "From now on..."
```

**Implementation:**
```python
import spacy
import re

DECISION_PATTERNS = [
    r"\b(decided|choosing|going with|settled on)\b",
    r"\b(always|never|must|should not)\s+\w+",
    r"^(Let's|We'll|I'll)\s+\w+",
    r"\b(rule|principle|policy):\s+",
]

def extract_decisions(text):
    matches = []
    for pattern in DECISION_PATTERNS:
        matches.extend(re.finditer(pattern, text, re.IGNORECASE))
    
    # Extract sentence containing match + context
    sentences = sent_tokenize(text)
    decision_sentences = [s for s in sentences if any(m.group() in s for m in matches)]
    
    return decision_sentences
```

### Contextual Classification

**Use Named Entity Recognition + Dependency Parsing:**
```python
nlp = spacy.load("en_core_web_sm")

def classify_decision(sentence):
    doc = nlp(sentence)
    
    # Extract: WHO decided WHAT
    subject = [tok for tok in doc if tok.dep_ == "nsubj"]
    action = [tok for tok in doc if tok.pos_ == "VERB"]
    object = [tok for tok in doc if tok.dep_ in ["dobj", "attr"]]
    
    return {
        "who": subject[0].text if subject else None,
        "action": action[0].text if action else None,
        "what": object[0].text if object else None,
        "full_text": sentence
    }
```

### Prioritization

**Score decisions by impact:**
- Mentions of "always/never" → High priority (behavioral axiom)
- Mentions of specific tools/workflows → Medium priority (operational)
- Preferences ("I prefer...") → Low priority (nice-to-know)

---

## 3. Automatic Axiom Generation from Recurring Patterns

### Current Rule: 3+ Observations = Axiom Candidate

**Problems:**
- Manual counting
- No temporal weighting (old vs. recent)
- No contradiction detection

### Improved Axiom Pipeline

#### Stage 1: Pattern Aggregation
```
For each detected pattern cluster:
1. Count occurrences across sessions
2. Weight recent observations higher (exponential decay)
3. Check for contradictions (opposite statements)
4. Calculate confidence score
```

**Weighting Formula:**
```python
import math
from datetime import datetime, timedelta

def calculate_confidence(observations):
    total_weight = 0
    for obs in observations:
        days_old = (datetime.now() - obs.timestamp).days
        weight = math.exp(-days_old / 30)  # 30-day half-life
        total_weight += weight
    
    # Require weighted sum >= 2.5 (approx 3 recent observations)
    return min(total_weight / 2.5, 1.0)
```

#### Stage 2: Contradiction Detection
```python
def check_contradictions(new_pattern, existing_axioms):
    # Compare embeddings
    new_emb = embed(new_pattern)
    
    for axiom in existing_axioms:
        axiom_emb = embed(axiom.text)
        similarity = cosine_similarity(new_emb, axiom_emb)
        
        # High similarity but opposite sentiment = contradiction
        if similarity > 0.7:
            if opposite_sentiment(new_pattern, axiom.text):
                return {"conflict": True, "axiom": axiom}
    
    return {"conflict": False}
```

#### Stage 3: Axiom Formulation
```
Template-based generation:

Pattern: "Agent should check email during heartbeats"
Observations: 5 (weighted: 3.2)
Category: Proactive behavior

Generated Axiom:
→ "During heartbeats, check email for urgent messages (established 2026-03-15, confidence: 85%)"

Format:
- Action statement (what to do)
- Context (when/where)
- Metadata (when established, confidence)
```

### Axiom Lifecycle

```
[Candidate] → (review) → [Active] → (contradicted/deprecated) → [Archived]
                ↓
           (rejected) → [Rejected]

- Candidates auto-generate, require human approval
- Active axioms used in MEMORY.md
- Archived axioms kept for historical context
```

---

## 4. Discord Bot Integration for Memory Updates

### Architecture Options

#### Option A: Webhook-Driven (Simple)
```
Discord webhook → Cloud function → Parse message → Update memory repo
```

**Pros:** Low latency, event-driven  
**Cons:** Requires external hosting, webhook management

#### Option B: Bot Polling (Current Setup Compatible)
```
Heartbeat (every 30min) → Check #patterns, #session-notes, #axioms → Process new messages
```

**Pros:** Works with existing heartbeat system  
**Cons:** Up to 30min delay, batched processing

#### Option C: Hybrid Event System (Recommended)
```
Discord bot (always-on) → Real-time message queue → Batch processor (hourly)
                                                    ↓
                                            Update staging branch
                                                    ↓
                                            Daily: Merge to main + update MEMORY.md
```

**Implementation:**
```javascript
// Discord.js bot
client.on('messageCreate', async (message) => {
  if (message.channel.name === 'patterns' || 
      message.channel.name === 'session-notes' ||
      message.channel.name === 'axioms') {
    
    // Add to processing queue
    await queue.add('memory-update', {
      content: message.content,
      author: message.author.id,
      channel: message.channel.name,
      timestamp: message.createdAt
    });
  }
});

// Worker process (runs every hour)
queue.process('memory-update', async (job) => {
  const entries = await queue.getWaiting();
  
  // Batch process
  const patterns = extractPatterns(entries);
  const decisions = extractDecisions(entries);
  
  // Update staging files
  await updateMemoryStaging(patterns, decisions);
});
```

### Channel-Specific Processing

**#patterns:**
- Feed into pattern detection pipeline
- Auto-categorize by topic (tools, behavior, preferences)
- Flag for axiom candidacy if recurring

**#session-notes:**
- Extract decisions using NLP decision markers
- Link to date-stamped memory files
- Summarize key takeaways

**#axioms:**
- Direct axiom proposals (human-curated)
- Higher trust level → faster approval
- Still check for contradictions

---

## 5. Scheduled vs Event-Driven Memory Maintenance

### Comparison Matrix

| Aspect | Scheduled (Cron/Heartbeat) | Event-Driven (Webhook/Queue) |
|--------|---------------------------|------------------------------|
| **Latency** | 5-30 minutes | Seconds to minutes |
| **Resource Usage** | Predictable, bursty | Variable, continuous |
| **Complexity** | Low (single script) | Medium (queue + workers) |
| **Batching** | Natural (all pending at once) | Must implement explicitly |
| **Failure Handling** | Simple retry on next run | Needs dead-letter queue |
| **Best For** | Daily summaries, non-urgent | Real-time updates, alerts |

### Recommended Hybrid Approach

**Event-Driven (Real-Time):**
- Collect messages from Discord channels
- Pattern detection on incoming messages
- Urgent decision flagging (e.g., "Never do X again!")

**Scheduled (Batch Processing):**
- Hourly: Aggregate patterns, run clustering
- Daily: Update MEMORY.md with new axioms
- Weekly: Review axiom candidates, prune old patterns

**Implementation Timeline:**
```
00:00-23:59 → Events queued in real-time
Every hour  → Process queue, extract patterns
Daily 02:00 → Generate axiom candidates
Daily 08:00 → Commit memory updates, notify human
Weekly Sun  → Review report, prune archives
```

### Preventing Spam/Noise

**Rate Limiting:**
```python
from collections import defaultdict
import time

recent_patterns = defaultdict(list)

def should_process_pattern(pattern_text):
    # Deduplicate within 1-hour window
    pattern_hash = hash(pattern_text.lower().strip())
    now = time.time()
    
    recent_patterns[pattern_hash] = [
        t for t in recent_patterns[pattern_hash] 
        if now - t < 3600
    ]
    
    if len(recent_patterns[pattern_hash]) >= 3:
        return False  # Already saw this 3x in past hour
    
    recent_patterns[pattern_hash].append(now)
    return True
```

**Quality Filters:**
- Minimum message length (>10 words for patterns)
- Ignore bot messages (unless explicitly whitelisted)
- Require human confirmation for axioms affecting safety

---

## 6. Proposed Automation Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Discord Channels                          │
│  #patterns | #session-notes | #axioms | #general            │
└────────────────────┬────────────────────────────────────────┘
                     │ (real-time events)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Message Queue (Redis/BullMQ)                    │
│  - Deduplicate within 1hr window                            │
│  - Tag with channel, timestamp, author                      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌──────────────────┐    ┌──────────────────┐
│ Pattern Detector │    │ Decision Extractor│
│ - Embeddings     │    │ - NLP markers     │
│ - Clustering     │    │ - Context parse   │
└────────┬─────────┘    └────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Pattern Database (ChromaDB)                     │
│  - Store: text, embedding, timestamp, category, count       │
│  - Query: similar patterns, frequency, temporal trends      │
└────────────────────┬────────────────────────────────────────┘
                     │ (hourly batch)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│               Axiom Generator                                │
│  1. Query patterns with count >= 3, weighted_score >= 2.5   │
│  2. Check contradictions against existing axioms            │
│  3. Generate axiom text from template                       │
│  4. Flag for human review                                   │
└────────────────────┬────────────────────────────────────────┘
                     │ (daily 02:00)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Memory Update Pipeline                          │
│  1. Review axiom candidates                                 │
│  2. Update MEMORY.md (insert under appropriate section)     │
│  3. Commit to git with summary                              │
│  4. Post summary to Discord (optional)                      │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
workspace/
├── memory/
│   ├── YYYY-MM-DD.md              # Daily raw logs (unchanged)
│   ├── patterns-detected.json     # Auto-generated pattern DB
│   ├── axiom-candidates.json      # Pending human review
│   └── axiom-history.json         # Accepted/rejected log
├── MEMORY.md                       # Curated long-term memory
└── automation/
    ├── pattern-detector.py         # Embedding + clustering
    ├── decision-extractor.py       # NLP decision parsing
    ├── axiom-generator.py          # Template-based generation
    └── memory-updater.py           # Git commit + MEMORY.md update
```

---

## 7. Migration Path: Manual → Automated

### Phase 1: Observation (Weeks 1-2)
**Goal:** Collect baseline data without changing current workflow

- Deploy pattern detector in "observe-only" mode
- Log detected patterns to `patterns-detected.json`
- Compare manual vs. auto-detected patterns
- Tune thresholds (similarity, frequency, temporal weighting)

**Success Metrics:**
- 80%+ recall (auto-detector finds manually-noted patterns)
- <20% false positive rate (auto-detected junk)

### Phase 2: Assisted (Weeks 3-4)
**Goal:** Automation suggests, human confirms

- Auto-generate axiom candidates
- Present in Discord (or daily summary) for review
- Human approves/rejects via reaction or command
- Track acceptance rate

**Success Metrics:**
- 50%+ of candidates accepted
- <5 minutes/day human review time

### Phase 3: Semi-Automated (Weeks 5-8)
**Goal:** Auto-commit low-risk updates, flag high-impact for review

- Low-risk: Tool preferences, scheduling tweaks → auto-commit
- High-risk: Safety rules, external communication → require approval
- Implement confidence thresholds (>90% confidence = auto-commit)

**Success Metrics:**
- 70%+ of updates auto-committed
- Zero safety incidents

### Phase 4: Fully Automated (Week 9+)
**Goal:** Hands-off memory maintenance with audit trail

- All updates auto-committed to staging branch
- Daily summary email/Discord post
- Human reviews git diff weekly
- Rollback mechanism for bad updates

**Success Metrics:**
- <30 minutes/week human oversight
- MEMORY.md stays current within 24 hours of new patterns

---

## 8. Comparison to Current Setup

### Current Setup
✅ **Strengths:**
- Simple, no infrastructure
- Human-in-loop prevents bad updates
- Heartbeat rhythm aligns with existing workflow

❌ **Weaknesses:**
- Manual bottleneck (requires human time every heartbeat)
- Inconsistent (skipped when busy)
- No semantic pattern detection
- Misses patterns across long time spans

### Proposed Automated Setup
✅ **Improvements:**
- Continuous monitoring (no gaps)
- Semantic pattern matching (catches paraphrasing)
- Temporal weighting (recent > old)
- Contradiction detection (prevents conflicts)
- Audit trail (git history of all changes)

⚠️ **New Risks:**
- Complexity (more moving parts)
- False positives (noisy auto-generated axioms)
- Dependency on external services (embeddings, queue)

**Mitigation:**
- Start with Phase 1 (observe-only)
- Keep human review for high-impact axioms
- Fallback to manual if automation fails

---

## 9. Recommended Next Steps

### Immediate (This Week)
1. ✅ Read this research document
2. 🔧 Set up basic pattern detector:
   ```bash
   pip install sentence-transformers scikit-learn
   python automation/pattern-detector.py --observe-only
   ```
3. 📊 Run on existing `memory/*.md` files to establish baseline

### Short-Term (Next 2 Weeks)
4. 🤖 Deploy Discord bot with message queue
5. 🧪 Test decision extraction on #session-notes channel
6. 📝 Create axiom candidate review UI (Discord commands or simple web page)

### Medium-Term (Next Month)
7. 🚀 Launch Phase 2 (assisted mode)
8. 📈 Tune thresholds based on acceptance rate
9. 🔄 Implement git-based staging workflow

### Long-Term (2-3 Months)
10. 🤖 Full automation with confidence-based gating
11. 📊 Analytics dashboard (pattern trends, axiom growth, coverage)
12. 🧠 Explore LLM-based axiom summarization (GPT-4 for high-quality phrasing)

---

## 10. Open Questions & Considerations

### Technical
- **Embedding model:** Local (fast, private) vs. API (better quality)?
- **Storage:** File-based JSON vs. SQLite vs. vector DB?
- **Hosting:** Run on existing OpenClaw instance or separate service?

### Workflow
- **Review frequency:** Daily vs. weekly summary?
- **Approval UX:** Discord reactions vs. slash commands vs. web UI?
- **Rollback:** How far back can we revert? (Git history vs. manual snapshots)

### Philosophy
- **How much automation is too much?** Should some axioms always require human approval?
- **Memory drift:** If auto-generated axioms accumulate, does MEMORY.md become bloated?
- **Trust calibration:** How do we ensure agent doesn't over-rely on noisy patterns?

---

## 11. Code Snippets

### Pattern Detector (Minimal Implementation)

```python
#!/usr/bin/env python3
"""
pattern-detector.py - Detect recurring patterns from memory logs
"""

from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

# Load embedding model (384-dim, fast)
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_memory_logs(memory_dir, days=30):
    """Load last N days of memory logs"""
    logs = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        log_file = Path(memory_dir) / f"{date.strftime('%Y-%m-%d')}.md"
        if log_file.exists():
            logs.append({
                'date': date,
                'text': log_file.read_text()
            })
    return logs

def extract_sentences(logs):
    """Split logs into sentences with metadata"""
    sentences = []
    for log in logs:
        # Simple sentence split (improve with spacy for production)
        raw_sentences = re.split(r'[.!?]\s+', log['text'])
        for sent in raw_sentences:
            if len(sent) > 20:  # Filter very short
                sentences.append({
                    'text': sent.strip(),
                    'date': log['date'],
                    'embedding': None
                })
    return sentences

def detect_patterns(sentences, similarity_threshold=0.8, min_cluster_size=3):
    """Cluster sentences by semantic similarity"""
    # Generate embeddings
    texts = [s['text'] for s in sentences]
    embeddings = model.encode(texts)
    
    # Cluster with DBSCAN
    clustering = DBSCAN(
        eps=1 - similarity_threshold,  # Convert similarity to distance
        min_samples=min_cluster_size,
        metric='cosine'
    )
    labels = clustering.fit_predict(embeddings)
    
    # Group by cluster
    patterns = {}
    for idx, label in enumerate(labels):
        if label == -1:  # Noise
            continue
        if label not in patterns:
            patterns[label] = []
        patterns[label].append(sentences[idx])
    
    return patterns

def calculate_pattern_confidence(pattern_sentences):
    """Weight by recency and frequency"""
    total_weight = 0
    for sent in pattern_sentences:
        days_old = (datetime.now() - sent['date']).days
        weight = np.exp(-days_old / 30)  # 30-day half-life
        total_weight += weight
    
    # Normalize to 0-1 scale (assume max 5 recent observations)
    return min(total_weight / 2.5, 1.0)

def format_pattern(cluster_id, sentences):
    """Create human-readable pattern summary"""
    # Use most recent sentence as representative
    sentences.sort(key=lambda s: s['date'], reverse=True)
    representative = sentences[0]['text']
    
    dates = [s['date'].strftime('%Y-%m-%d') for s in sentences]
    confidence = calculate_pattern_confidence(sentences)
    
    return {
        'id': cluster_id,
        'text': representative,
        'occurrences': len(sentences),
        'dates': dates,
        'confidence': confidence,
        'first_seen': min(s['date'] for s in sentences).isoformat(),
        'last_seen': max(s['date'] for s in sentences).isoformat()
    }

def main():
    memory_dir = Path.home() / '.openclaw' / 'workspace-general-purpose' / 'memory'
    output_file = memory_dir / 'patterns-detected.json'
    
    # Load logs
    print("Loading memory logs...")
    logs = load_memory_logs(memory_dir, days=30)
    
    # Extract sentences
    print(f"Extracting sentences from {len(logs)} log files...")
    sentences = extract_sentences(logs)
    print(f"Found {len(sentences)} candidate sentences")
    
    # Detect patterns
    print("Detecting patterns (this may take a minute)...")
    patterns = detect_patterns(sentences, similarity_threshold=0.80, min_cluster_size=3)
    
    # Format results
    results = []
    for cluster_id, cluster_sentences in patterns.items():
        pattern = format_pattern(cluster_id, cluster_sentences)
        if pattern['confidence'] >= 0.6:  # Only high-confidence patterns
            results.append(pattern)
    
    # Sort by confidence
    results.sort(key=lambda p: p['confidence'], reverse=True)
    
    # Save
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\n✅ Detected {len(results)} patterns")
    print(f"📁 Saved to {output_file}")
    
    # Print top 5
    print("\n🔍 Top 5 Patterns:")
    for i, pattern in enumerate(results[:5], 1):
        print(f"\n{i}. [{pattern['confidence']:.0%} confidence, {pattern['occurrences']} occurrences]")
        print(f"   {pattern['text'][:100]}...")
        print(f"   Dates: {', '.join(pattern['dates'][:3])}{'...' if len(pattern['dates']) > 3 else ''}")

if __name__ == '__main__':
    main()
```

### Decision Extractor

```python
#!/usr/bin/env python3
"""
decision-extractor.py - Extract decisions from session notes
"""

import re
from pathlib import Path
from datetime import datetime

DECISION_PATTERNS = [
    r"\b(decided|choosing|going with|settled on|picked)\b",
    r"\b(always|never|must|should not|shouldn't|can't)\s+\w+",
    r"^(Let's|We'll|I'll|Will|From now on)\s+",
    r"\b(rule|principle|policy|guideline):\s+",
    r"→",  # Arrow notation often indicates decisions
]

def extract_decisions(text):
    """Find sentences containing decision markers"""
    decisions = []
    
    # Split into sentences
    sentences = re.split(r'[.!?]\n', text)
    
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:
            continue
            
        # Check for decision markers
        for pattern in DECISION_PATTERNS:
            if re.search(pattern, sent, re.IGNORECASE):
                decisions.append(sent)
                break  # Don't double-count
    
    return decisions

def categorize_decision(decision_text):
    """Classify decision type"""
    lower = decision_text.lower()
    
    if any(word in lower for word in ['always', 'never', 'must', 'rule']):
        return 'behavioral-axiom'
    elif any(word in lower for word in ['prefer', 'like', 'better']):
        return 'preference'
    elif any(word in lower for word in ['tool', 'command', 'use']):
        return 'operational'
    else:
        return 'general'

def main():
    memory_dir = Path.home() / '.openclaw' / 'workspace-general-purpose' / 'memory'
    
    # Process today's log
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = memory_dir / f"{today}.md"
    
    if not log_file.exists():
        print(f"❌ No log file for {today}")
        return
    
    text = log_file.read_text()
    decisions = extract_decisions(text)
    
    print(f"📋 Found {len(decisions)} decisions in {today}.md:\n")
    
    for decision in decisions:
        category = categorize_decision(decision)
        print(f"[{category}] {decision}\n")

if __name__ == '__main__':
    main()
```

---

## Conclusion

**Key Takeaways:**

1. **Hybrid approach wins:** Combine semantic clustering + keyword matching for robust pattern detection
2. **Progressive automation:** Start observe-only, gradually increase autonomy with confidence gating
3. **Event + scheduled:** Real-time collection, batch processing, daily commits
4. **Human-in-loop for high-impact:** Safety axioms always require approval
5. **Git as audit trail:** Every change tracked, easy rollback

**Expected Impact:**
- **Time savings:** 80% reduction in manual memory maintenance (from ~30min/day to ~5min/day)
- **Coverage:** 24/7 monitoring vs. intermittent heartbeat checks
- **Quality:** Semantic pattern detection catches nuances humans might miss
- **Consistency:** No skipped updates due to busy schedule

**Risk Mitigation:**
- Phased rollout with observation periods
- Confidence-based gating (low confidence = human review)
- Contradiction detection prevents conflicting axioms
- Git history enables quick rollback

**Next Action:** Implement pattern detector in observe-only mode, run on historical data, tune thresholds.

---

*End of Research Document*
