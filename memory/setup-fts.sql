-- OpenClaw Memory Full-Text Search Setup
-- SQLite FTS5 (Full-Text Search) index for MEMORY.md and daily logs

-- Create FTS5 virtual table for memory content
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
  source,           -- File path (MEMORY.md, memory/2026-03-20.md, etc.)
  section,          -- Section name (Active Axioms, Key Decisions, etc.)
  content,          -- Actual text content
  timestamp,        -- When this was added/updated
  category,         -- axiom|decision|project|learning|pattern
  tokenize = 'porter unicode61'
);

-- Create metadata table for tracking indexed files
CREATE TABLE IF NOT EXISTS memory_index_meta (
  file_path TEXT PRIMARY KEY,
  last_indexed INTEGER,  -- Unix timestamp
  file_hash TEXT,        -- SHA256 of file content
  entry_count INTEGER    -- Number of FTS entries for this file
);

-- Create axioms table for structured queries
CREATE TABLE IF NOT EXISTS axioms (
  id TEXT PRIMARY KEY,           -- AXIOM-001, AXIOM-037, etc.
  number INTEGER,                -- Numeric part for sorting
  category TEXT,                 -- workflow, research, technical, etc.
  title TEXT,                    -- Short name
  rule TEXT,                     -- The actual rule
  observed TEXT,                 -- What led to this
  applied TEXT,                  -- When to use it
  added_date TEXT,               -- ISO date
  status TEXT DEFAULT 'active',  -- active|proposed|deprecated
  access_count INTEGER DEFAULT 0 -- Track usage
);

-- Create decisions table
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  title TEXT,
  description TEXT,
  category TEXT,
  impact TEXT
);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
  name TEXT PRIMARY KEY,
  description TEXT,
  location TEXT,
  status TEXT,
  last_updated TEXT
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_axioms_category ON axioms(category);
CREATE INDEX IF NOT EXISTS idx_axioms_status ON axioms(status);
CREATE INDEX IF NOT EXISTS idx_axioms_access ON axioms(access_count DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_date ON decisions(date DESC);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- Triggers to update FTS when structured tables change
CREATE TRIGGER IF NOT EXISTS axioms_fts_insert AFTER INSERT ON axioms BEGIN
  INSERT INTO memory_fts(source, section, content, timestamp, category)
  VALUES ('axioms_table', NEW.id, NEW.title || ' ' || NEW.rule || ' ' || COALESCE(NEW.observed, ''), datetime('now'), 'axiom');
END;

CREATE TRIGGER IF NOT EXISTS axioms_fts_update AFTER UPDATE ON axioms BEGIN
  DELETE FROM memory_fts WHERE source = 'axioms_table' AND section = OLD.id;
  INSERT INTO memory_fts(source, section, content, timestamp, category)
  VALUES ('axioms_table', NEW.id, NEW.title || ' ' || NEW.rule || ' ' || COALESCE(NEW.observed, ''), datetime('now'), 'axiom');
END;
