# Memory Management Research for AI Agent Systems
**Research Date:** March 20, 2026  
**Subagent Task Output**

## Executive Summary

This research examines memory management best practices across leading AI agent frameworks (LangChain, Letta/MemGPT, Mem0, AutoGPT) and compares them against OpenClaw's current two-tier system (daily logs + MEMORY.md + Axioms). The analysis reveals several opportunities to enhance our memory architecture through semantic search, structured archival, and better retrieval patterns.

**Key Findings:**
- Modern agent frameworks prioritize **vector-based semantic search** over flat-file approaches
- **Hybrid architectures** (structured DB + curated files) outperform single-method systems
- **Memory pruning/archival** is essential for long-running agents
- **Context awareness** (knowing token budget) enables better memory decisions
- **Workspace-based memory** (like OpenMemory) enables team collaboration

---

## 1. How Other Frameworks Handle Long-Term Memory

### 1.1 Letta (formerly MemGPT)
**Architecture:** Memory blocks + persistent storage + self-editing memory

**Key Features:**
- **Memory blocks**: Structured chunks (human, persona, core context) that agents can read/write
- **Self-improving memory**: Agents decide when to update their own memory
- **Multi-context workflow**: Save state before context window exhausts, resume in new window
- **Context awareness**: Models track remaining token budget to manage memory operations

**Memory Pattern:**
```python
memory_blocks=[
    {"label": "human", "value": "Name: X. Preferences: Y"},
    {"label": "persona", "value": "I am an agent who..."},
    {"label": "workspace", "value": "Current project state..."}
]
```

**Strengths:**
- Agents autonomously manage their memory
- Natural transitions across context windows
- Memory is queryable via API
- Structured format enables programmatic access

**Weaknesses:**
- Requires database infrastructure
- More complex to set up than flat files
- Memory can become stale without pruning

---

### 1.2 Mem0
**Architecture:** Vector database + automatic memory extraction + semantic search

**Key Features:**
- **Automatic extraction**: LLM analyzes conversations and extracts memories
- **Semantic search**: Vector embeddings enable fuzzy retrieval
- **User/Agent/Session scoping**: Memories tied to entities
- **CRUD operations**: Full add/search/update/delete API
- **Categories & metadata**: Tag-based organization

**Memory Pattern:**
```python
# Add memory from conversation
client.add(messages, user_id="user123")

# Semantic search
results = client.search(
    "dietary restrictions?", 
    filters={"user_id": "user123"}
)
```

**Strengths:**
- Zero manual curation required
- Fuzzy semantic search (finds related memories, not just keywords)
- Multi-user support out of the box
- Platform handles memory lifecycle

**Weaknesses:**
- Requires API key / external service (Platform version)
- Less transparent than file-based memory
- Risk of extracting incorrect or irrelevant memories
- Token cost for memory operations

---

### 1.3 LangChain / Deep Agents
**Architecture:** Context compression + virtual filesystem + subagent spawning

**Key Features:**
- **Automatic compression**: Long conversations auto-compact as context fills
- **Durable execution**: State persists across API calls
- **Multi-window workflows**: Designed for tasks spanning multiple context resets
- **LangSmith tracing**: Debug memory and state transitions

**Memory Pattern:**
```python
# Built-in context management
agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[...],
    system_prompt="...",
    # Compression happens automatically
)
```

**Strengths:**
- Minimal manual memory management
- Built-in observability (LangSmith)
- Scales to long-horizon tasks

**Weaknesses:**
- Less control over what's remembered
- Compression can lose nuance
- Requires LangChain ecosystem

---

### 1.4 AutoGPT
**Architecture:** Agent loops + marketplace agents + workflow builder

**Key Features:**
- **External triggers**: Agents can run continuously, triggered by events
- **Workflow blocks**: Visual agent builder
- **Pre-built agents**: Library of ready-to-use patterns

**Memory Pattern:**
- Less focused on memory primitives
- More focused on workflow orchestration
- State stored in agent execution context

**Strengths:**
- Good for event-driven workflows
- Low-code interface

**Weaknesses:**
- Memory is implicit in workflow state
- Less sophisticated than Letta/Mem0 for long-term recall

---

## 2. MEMORY.md vs Database Approaches

### 2.1 File-Based (MEMORY.md) — OpenClaw Current Approach

**Pros:**
✅ **Human-readable**: Easy to inspect, audit, and understand  
✅ **Version control friendly**: Git tracks changes, diffs are meaningful  
✅ **No infrastructure**: Works offline, no DB setup  
✅ **Transparent**: User sees exactly what agent remembers  
✅ **Portable**: Plain markdown travels anywhere  
✅ **Privacy**: Stays local, no external services  

**Cons:**
❌ **Linear search only**: Can't semantically search ("what did I say about X?")  
❌ **Manual curation required**: Agent must decide what to keep  
❌ **Token overhead**: Entire file loaded into context (not paginated)  
❌ **No multi-user scoping**: Single global memory  
❌ **Hard to query programmatically**: No structured query interface  
❌ **Scaling issues**: 1000+ line MEMORY.md becomes unwieldy  

**Best for:**
- Single-user agents
- Privacy-critical deployments
- Explainability requirements
- Simple setups

---

### 2.2 Database Approaches (Letta, Mem0)

**Pros:**
✅ **Semantic search**: Vector embeddings find related memories  
✅ **Structured queries**: Filter by user, date, category, etc.  
✅ **Scalable**: Handle millions of memories  
✅ **Multi-entity**: User/agent/session scoping built-in  
✅ **Automatic extraction**: LLM decides what to store  
✅ **CRUD operations**: Programmatic update/delete  

**Cons:**
❌ **Infrastructure required**: Need vector DB (Qdrant, Pinecone, Chroma)  
❌ **Less transparent**: User can't easily audit all memories  
❌ **External dependencies**: API keys, network calls  
❌ **Token cost**: Embedding generation + search  
❌ **Privacy concerns**: Data may leave local system  
❌ **Harder to debug**: Can't just `cat MEMORY.md`  

**Best for:**
- Multi-user platforms
- Long-running agents with large memory
- Production deployments
- Teams needing shared context

---

### 2.3 Hybrid Approach (Recommended)

**Combine the best of both:**

```
📁 memory/
  ├── MEMORY.md              # Curated long-term memories (human-readable)
  ├── YYYY-MM-DD.md          # Daily raw logs
  ├── memory.db              # SQLite for structured queries
  └── embeddings/            # Vector index for semantic search
```

**Pattern:**
1. **Daily logs** → raw append-only captures
2. **Agent periodically reviews** → extracts key learnings
3. **Stores in both**:
   - `MEMORY.md` for human readability (top 50-100 memories)
   - `memory.db` for structured queries (dates, categories, entities)
   - `embeddings/` for semantic search
4. **Pruning policy** → archive old daily logs, keep MEMORY.md lean

**Benefits:**
- Human readability + semantic search
- Privacy (local SQLite) + scalability
- Git-friendly (MEMORY.md) + structured queries (DB)

---

## 3. Semantic Search Integration Patterns

### 3.1 Standalone Vector DB

**Setup:**
```bash
# Local vector DB (Chroma, Qdrant)
pip install chromadb

# Store embeddings
from chromadb import Client
client = Client()
collection = client.create_collection("memories")

# Add memory
collection.add(
    documents=["User prefers dark mode"],
    metadatas=[{"date": "2026-03-20", "category": "preferences"}],
    ids=["mem-001"]
)

# Semantic search
results = collection.query(
    query_texts=["ui preferences"],
    n_results=5
)
```

**When to use:**
- Large memory corpus (1000+ entries)
- Need fuzzy retrieval
- Multi-modal memories (text + images)

---

### 3.2 Lightweight Embedding Search (No DB)

**Setup:**
```python
# Use OpenAI/Anthropic embeddings + local numpy
import numpy as np
from anthropic import Anthropic

# Generate embeddings for MEMORY.md sections
embeddings = []
for memory_chunk in memory_sections:
    embedding = client.embeddings.create(
        input=memory_chunk,
        model="text-embedding-3-small"
    )
    embeddings.append(embedding.data[0].embedding)

# Search
query_embedding = get_embedding(user_query)
similarities = np.dot(embeddings, query_embedding)
top_matches = np.argsort(similarities)[-5:]
```

**When to use:**
- Small-to-medium memory (< 1000 entries)
- Want semantic search without DB overhead
- Willing to regenerate embeddings periodically

---

### 3.3 Hybrid File + Search

**Pattern:**
```python
# memory_index.json (lightweight metadata)
{
  "memories": [
    {
      "id": "001",
      "text": "User is allergic to nuts",
      "category": "health",
      "date": "2026-03-01",
      "embedding": [0.23, 0.45, ...],  # 1536-dim vector
      "source_file": "memory/2026-03-01.md",
      "line": 42
    }
  ]
}
```

**Search:**
1. Embed query
2. Find top-k similar embeddings in `memory_index.json`
3. Read source lines from original markdown files
4. Return human-readable context

**Benefits:**
- Fast semantic search
- Human can still read/edit markdown
- Hybrid of file transparency + vector search

---

## 4. Memory Pruning & Archival Strategies

### 4.1 Time-Based Archival

**Strategy:**
```bash
memory/
  ├── active/
  │   ├── MEMORY.md           # Top 100 memories (most relevant)
  │   └── 2026-03-*.md        # Last 30 days
  ├── archive/
  │   ├── 2026-Q1.md.gz       # Compressed quarterly archives
  │   └── 2025-*.md.gz
  └── cold/
      └── pre-2025.db         # Searchable but not in context
```

**Policy:**
- **Active**: Last 30 days + MEMORY.md (always in context)
- **Archive**: 30-365 days (load on-demand via search)
- **Cold storage**: 1+ year old (queryable DB, not in prompt)

**Implementation:**
```bash
# Nightly cron job
0 2 * * * cd ~/.openclaw/memory && ./archive-old-logs.sh
```

```bash
#!/bin/bash
# archive-old-logs.sh
find active/ -name "*.md" -mtime +30 -exec gzip {} \;
mv active/*.gz archive/
```

---

### 4.2 Importance-Based Pruning

**Strategy:**
- Agent scores each memory by "importance" (1-10)
- Prune low-importance memories after N days
- Keep high-importance memories indefinitely

**Schema:**
```json
{
  "memory_id": "abc123",
  "text": "User's birthday is July 15",
  "importance": 9,
  "last_accessed": "2026-03-20",
  "access_count": 12,
  "created": "2025-06-01"
}
```

**Pruning logic:**
```python
# Delete if:
# - importance < 5 AND not accessed in 90 days
# - importance < 3 AND not accessed in 30 days
# - importance >= 8 → keep forever

if memory.importance < 5 and days_since_access > 90:
    archive_memory(memory)
elif memory.importance < 3 and days_since_access > 30:
    archive_memory(memory)
```

---

### 4.3 LRU (Least Recently Used) Eviction

**Strategy:**
- Track when each memory was last retrieved
- Evict least-recently-used when memory limit hit

**Implementation:**
```python
class MemoryCache:
    def __init__(self, max_memories=500):
        self.cache = OrderedDict()
        self.max_size = max_memories
    
    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)  # Mark as recently used
            return self.cache[key]
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            oldest = next(iter(self.cache))
            self.archive(self.cache.pop(oldest))
```

---

### 4.4 Compression via Summarization

**Strategy:**
- Periodically summarize old memories
- Replace 10 detailed memories with 1 compressed summary

**Example:**
```
# Before (10 memories, 500 tokens)
- User ordered coffee on 2026-01-05
- User ordered coffee on 2026-01-12
- User ordered coffee on 2026-01-19
...

# After (1 memory, 50 tokens)
- User orders coffee weekly, prefers oat milk lattes
```

**Implementation:**
```python
# Weekly cron: summarize last week's activity
weekly_logs = read_logs("2026-03-13", "2026-03-20")
summary = llm.summarize(weekly_logs)
append_to_memory_md(summary)
archive(weekly_logs)
```

---

## 5. Retrieval-Augmented Memory (RAG for Agents)

### 5.1 Pattern: RAG-Enhanced Context

**Flow:**
```
1. User message arrives
2. Embed user query
3. Search memory DB for top-k relevant memories
4. Inject into system prompt:
   <relevant_memories>
     - User prefers dark mode
     - User is allergic to nuts
   </relevant_memories>
5. Agent responds with full context
```

**Benefits:**
- Agent sees only relevant memories (not entire MEMORY.md)
- Scales to large memory corpus
- Token-efficient

**Example:**
```python
def build_prompt_with_memory(user_message):
    # Semantic search
    relevant = memory_db.search(user_message, top_k=5)
    
    # Inject into prompt
    memory_context = "\n".join([f"- {m.text}" for m in relevant])
    
    system_prompt = f"""
    <relevant_memories>
    {memory_context}
    </relevant_memories>
    
    You are a helpful assistant. Use the memories above to personalize your response.
    """
    
    return system_prompt
```

---

### 5.2 Two-Tier Memory System (Current + Enhanced)

**Current OpenClaw:**
```
Tier 1: Daily logs (memory/YYYY-MM-DD.md) → append-only raw logs
Tier 2: MEMORY.md → curated long-term memories
```

**Enhanced Version:**
```
Tier 1: Daily logs (raw, append-only)
Tier 2: MEMORY.md (curated, human-readable, top 100)
Tier 3: memory.db (structured, queryable, all historical)
Tier 4: embeddings/ (semantic search index)
```

**Retrieval Strategy:**
1. **Always load**: MEMORY.md (top curated memories)
2. **On-demand via RAG**: Search `memory.db` + `embeddings/` for related context
3. **Archive access**: Query cold storage only when explicitly requested

---

### 5.3 Contextual Memory Injection

**Strategy:**
- Different memory subsets for different contexts

**Examples:**
```python
# Coding task → load technical preferences
if task_type == "coding":
    memory_filter = {"category": "technical"}

# Personal chat → load personal context
elif task_type == "chat":
    memory_filter = {"category": ["personal", "preferences"]}

# Research → load past research notes
elif task_type == "research":
    memory_filter = {"tags": ["research", "articles"]}
```

**Benefits:**
- Reduce token overhead
- Avoid irrelevant memories polluting context
- Agent stays focused

---

## 6. Comparison with OpenClaw's Current Setup

### Current Architecture

```
memory/
  ├── YYYY-MM-DD.md      # Daily raw logs (append-only)
  └── MEMORY.md          # Curated long-term memories

Axioms:
  - 37+ active axioms
  - Patterns documented in Discord (#patterns, #axioms)
  - Session notes in #session-notes
```

**Strengths:**
✅ Human-readable  
✅ Git-friendly  
✅ Privacy-preserving (local)  
✅ Simple to understand  
✅ Works offline  

**Weaknesses:**
❌ No semantic search  
❌ Manual curation burden  
❌ Token overhead (loads entire MEMORY.md)  
❌ No structured queries  
❌ Hard to scale past ~1000 memories  
❌ Axioms disconnected from memory system  

---

## 7. Actionable Recommendations

### 7.1 **Immediate Wins (Low Effort, High Impact)**

#### 1. Add Memory Metadata to MEMORY.md
**Change:**
```markdown
<!-- BEFORE -->
- User prefers dark mode

<!-- AFTER -->
- User prefers dark mode  
  *[category: ui/preferences | added: 2026-03-01 | importance: 7]*
```

**Benefits:**
- Enables future structured extraction
- Helps with pruning decisions
- No code changes required

---

#### 2. Create `memory/index.md` with Categorized TOC
**File:** `memory/index.md`
```markdown
# Memory Index

## Categories
- [Technical Preferences](#technical)
- [Personal Context](#personal)
- [Project History](#projects)
- [Axioms & Patterns](#axioms)

## Technical
- Dark mode preference (2026-03-01)
- Prefers TypeScript over JavaScript (2026-02-15)
...
```

**Benefits:**
- Faster human lookup
- Agent can jump to relevant sections
- Reduces token overhead (load category, not full file)

---

#### 3. Implement Nightly Memory Review
**Cron job:**
```bash
# ~/.openclaw/cron/memory-review.sh
0 3 * * * cd ~/.openclaw && node scripts/review-memory.js
```

**Script: `scripts/review-memory.js`**
```javascript
// 1. Read yesterday's log
// 2. Extract key learnings (via LLM)
// 3. Append to MEMORY.md
// 4. Compress old logs (7+ days) to archive/
```

**Benefits:**
- Automate memory curation
- Prevent MEMORY.md from growing unbounded
- Agent maintains fresh context

---

### 7.2 **Medium Effort (Moderate Lift, High Value)**

#### 4. Add Lightweight Semantic Search (SQLite FTS5)
**Setup:**
```bash
# Install dependencies
npm install better-sqlite3
```

**Schema:**
```sql
CREATE VIRTUAL TABLE memories USING fts5(
  id UNINDEXED,
  text,
  category,
  date,
  importance
);

INSERT INTO memories VALUES 
  ('mem-001', 'User prefers dark mode', 'ui', '2026-03-01', 8);
```

**Search:**
```javascript
const db = require('better-sqlite3')('memory.db');
const results = db.prepare(`
  SELECT * FROM memories 
  WHERE memories MATCH ? 
  ORDER BY rank LIMIT 5
`).all('dark mode preferences');
```

**Benefits:**
- Full-text search without vector DB
- Fast local queries
- No external API dependencies
- Queries like "what did I say about X?" work

---

#### 5. Integrate Axioms into Memory System
**Current:** Axioms are Discord-based (#axioms channel)  
**Proposed:** Store axioms in `memory/axioms.md` + sync with Discord

**File: `memory/axioms.md`**
```markdown
# Axioms (37 Active)

## Axiom 001: Memory Management
- **Rule:** Batch heartbeat checks (don't poll every 5 min)
- **Rationale:** Reduce API costs + token burn
- **Source:** Discord #axioms, 2026-02-10

## Axiom 002: Voice Usage
- **Rule:** Use voice (sag/ElevenLabs) for stories, not walls of text
- **Rationale:** More engaging for users
- **Source:** AGENTS.md, TOOLS.md
...
```

**Benefits:**
- Axioms accessible to agent in every session
- Version-controlled (git tracks changes)
- Agent can reference axioms in decision-making

---

#### 6. Implement Memory Access Tracking
**Add to memory schema:**
```json
{
  "memory_id": "abc123",
  "text": "...",
  "access_count": 5,
  "last_accessed": "2026-03-20"
}
```

**Usage:**
- Track which memories are frequently accessed → prioritize in MEMORY.md
- Prune never-accessed memories → archive
- Optimize context window (load frequently-used memories first)

---

### 7.3 **Long-Term Improvements (High Effort, Transformative)**

#### 7. Build Hybrid Memory System (File + DB + Embeddings)
**Architecture:**
```
memory/
  ├── MEMORY.md                 # Human-readable top 100
  ├── daily/YYYY-MM-DD.md       # Raw logs (append-only)
  ├── memory.db                 # SQLite FTS5 (structured queries)
  └── embeddings/
      ├── index.json            # Lightweight vector index
      └── vectors.bin           # Embedding storage
```

**Workflow:**
1. **Daily logs** → append raw events
2. **Nightly job** → extract key memories → store in both MEMORY.md and memory.db
3. **Weekly job** → generate embeddings → update `embeddings/index.json`
4. **Agent startup** → load MEMORY.md (curated) + query memory.db (structured) + search embeddings (semantic)

**Benefits:**
- Best of all worlds: human-readable + semantic search + structured queries
- Scales to 10,000+ memories
- Local (privacy-preserving)

---

#### 8. Implement Multi-Context Window Memory (Letta-style)
**Pattern:**
- Agent tracks remaining token budget
- Before context exhausts, saves state to `memory/session-state.json`
- On fresh context window, loads state + continues

**Implementation:**
```javascript
// Save state before context limit
if (contextTokens > MAX_TOKENS * 0.9) {
  saveState({
    progress: currentProgress,
    todos: remainingTasks,
    context: recentDecisions
  });
  compactContext();
}

// Resume in new window
if (sessionStateExists()) {
  const state = loadState();
  continueFrom(state);
}
```

**Benefits:**
- Enables long-horizon tasks (multi-hour coding sessions)
- Graceful context window transitions
- No lost work

---

#### 9. Add Memory Pruning Policies
**Policies:**
1. **Archive old daily logs** (30+ days → gzip)
2. **Prune low-importance memories** (importance < 5, not accessed in 90 days)
3. **Compress similar memories** (10 coffee orders → "User orders coffee weekly")
4. **Delete duplicate memories** (fuzzy deduplication)

**Automation:**
```bash
# Weekly cron job
0 4 * * 0 cd ~/.openclaw && node scripts/prune-memory.js
```

**Script:**
```javascript
// 1. Archive old logs
// 2. Score memories by importance + access frequency
// 3. Move low-scoring to archive/
// 4. Deduplicate similar entries
// 5. Regenerate embeddings index
```

---

#### 10. Enable Shared Memory (Team/Multi-Agent)
**Use Case:** Multiple agents/users share common knowledge base

**Architecture:**
```
memory/
  ├── personal/          # User-specific memories
  │   ├── user-123.md
  │   └── user-456.md
  ├── shared/            # Team knowledge
  │   ├── company-docs.md
  │   └── project-alpha.md
  └── agent-specific/    # Agent-learned patterns
      ├── agent-001.md
      └── agent-002.md
```

**Benefits:**
- Multi-user support
- Team collaboration
- Agent-specific vs. shared knowledge separation

---

## 8. Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
- [ ] Add metadata to MEMORY.md entries
- [ ] Create `memory/index.md` with categorized TOC
- [ ] Move Axioms to `memory/axioms.md`
- [ ] Implement nightly memory review (basic version)

**Expected Impact:** Better organization, easier manual lookup, automated curation starts

---

### Phase 2: Search Capabilities (Week 2-3)
- [ ] Set up SQLite FTS5 for full-text search
- [ ] Build `memory_search` tool for agent
- [ ] Implement memory access tracking
- [ ] Create memory pruning script (archive old logs)

**Expected Impact:** Agent can query memory semantically, token overhead reduced

---

### Phase 3: Hybrid System (Week 4-6)
- [ ] Add lightweight embeddings (OpenAI API or local model)
- [ ] Build RAG-style memory retrieval
- [ ] Implement importance-based pruning
- [ ] Create memory stats dashboard (usage, size, access patterns)

**Expected Impact:** Scales to large memory corpus, semantic search works well

---

### Phase 4: Advanced Features (Month 2+)
- [ ] Multi-context window state management
- [ ] Shared/team memory support
- [ ] Memory versioning (git-based time travel)
- [ ] Integration with Discord (#axioms, #patterns auto-sync)

**Expected Impact:** Production-grade memory system, team collaboration, long-horizon tasks

---

## 9. Metrics & Success Criteria

**Track:**
1. **Memory retrieval accuracy**: Can agent find relevant memories?
2. **Token overhead**: How many tokens spent on memory per session?
3. **Curation effort**: How much manual editing required?
4. **Pruning effectiveness**: How much memory archived vs. kept active?
5. **User satisfaction**: Does agent feel like it "remembers" things?

**Goals:**
- Reduce manual MEMORY.md curation by 80%
- Enable semantic search ("what did I say about X?")
- Keep active memory < 10k tokens
- Maintain human-readable transparency

---

## 10. Open Questions & Considerations

### Privacy
**Q:** Should we ever use external APIs (OpenAI embeddings, Mem0 Platform)?  
**A:** Only if user explicitly opts in. Default to local (SQLite FTS5, local embeddings).

### Axioms Integration
**Q:** How to keep Discord #axioms in sync with `memory/axioms.md`?  
**A:** Bidirectional sync: Discord → file (webhook), file → Discord (cron post).

### Multi-Agent Memory
**Q:** Should subagents share memory with main agent?  
**A:** Depends on use case. Research subagent: isolated. Coding subagent: shared project context.

### Token Budget
**Q:** How to balance memory richness vs. token cost?  
**A:** RAG-style retrieval (load only relevant memories), not full MEMORY.md dump.

---

## 11. Conclusion

**Current System Strengths:**
- Human-readable
- Privacy-preserving
- Git-friendly
- Simple

**Current System Weaknesses:**
- No semantic search
- Manual curation burden
- Scaling issues
- Disconnected from Axioms

**Recommended Path:**
1. **Short-term:** Add metadata, create index, automate nightly reviews
2. **Medium-term:** SQLite FTS5 search, memory tracking, Axioms integration
3. **Long-term:** Hybrid file+DB+embeddings, multi-context support, team memory

**Philosophy:**
> "The best memory system is one the user can understand, the agent can query, and scales gracefully."

Combine human-readable files (transparency) with structured DB (queryability) and semantic search (intelligence). Don't pick one—use all three.

---

## 12. References

### Frameworks Analyzed
- **Letta (MemGPT)**: https://docs.letta.com
- **Mem0**: https://docs.mem0.ai
- **LangChain**: https://docs.langchain.com
- **AutoGPT**: https://github.com/Significant-Gravitas/AutoGPT

### Key Concepts
- **Context awareness**: Claude 4.6 models track token budget
- **Multi-context workflows**: Save state, resume in fresh window
- **RAG for agents**: Retrieve relevant memories, not full corpus
- **Hybrid architectures**: File + DB + embeddings

### Relevant Documentation
- Anthropic long-context prompting: https://platform.claude.com/docs
- Vector search patterns: Chroma, Qdrant, FAISS
- SQLite FTS5: https://www.sqlite.org/fts5.html

---

**End of Research Report**  
*Generated by: Subagent (general-purpose)*  
*Date: March 20, 2026*
