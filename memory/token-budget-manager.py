#!/usr/bin/env python3
"""
OpenClaw Token Budget Manager
Allocates token budgets per agent, prevents resource starvation.
"""

import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent
BUDGETS_FILE = MEMORY_DIR / "token-budgets.json"

DEFAULT_BUDGETS = {
    "main": {
        "total": 150000,
        "reserved": True,
        "priority": "high"
    },
    "research": {
        "total": 50000,
        "reserved": False,
        "priority": "medium"
    },
    "quick-task": {
        "total": 10000,
        "reserved": False,
        "priority": "low"
    },
    "background": {
        "total": 20000,
        "reserved": False,
        "priority": "low"
    }
}

class TokenBudgetManager:
    def __init__(self):
        self.budgets_file = BUDGETS_FILE
        self._load()
    
    def _load(self):
        """Load budgets from file."""
        if self.budgets_file.exists():
            with open(self.budgets_file) as f:
                self.data = json.load(f)
        else:
            self.data = {
                "config": DEFAULT_BUDGETS,
                "usage": {},
                "sessions": {}
            }
            self._save()
    
    def _save(self):
        """Save budgets to file."""
        with open(self.budgets_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def allocate(self, session_id: str, agent_type: str = "research"):
        """Allocate budget for a new agent session."""
        if agent_type not in self.data['config']:
            print(f"Warning: Unknown agent type '{agent_type}', using 'research' budget")
            agent_type = "research"
        
        budget = self.data['config'][agent_type]['total']
        
        self.data['sessions'][session_id] = {
            "agentType": agent_type,
            "allocatedBudget": budget,
            "usedTokens": 0,
            "startedAt": datetime.now().isoformat(),
            "status": "active"
        }
        
        self._save()
        print(f"✓ Allocated {budget:,} tokens to {session_id} ({agent_type})")
        return budget
    
    def track_usage(self, session_id: str, tokens_used: int):
        """Track token usage for a session."""
        if session_id not in self.data['sessions']:
            print(f"Warning: Session {session_id} not allocated")
            return False
        
        session = self.data['sessions'][session_id]
        session['usedTokens'] = tokens_used
        
        # Check if over budget
        if tokens_used > session['allocatedBudget']:
            session['status'] = 'over_budget'
            print(f"⚠️  {session_id} over budget: {tokens_used:,}/{session['allocatedBudget']:,}")
            self._save()
            return False
        
        self._save()
        return True
    
    def get_budget_status(self, session_id: str):
        """Get current budget status for a session."""
        if session_id not in self.data['sessions']:
            return None
        
        session = self.data['sessions'][session_id]
        used = session['usedTokens']
        total = session['allocatedBudget']
        
        return {
            "sessionId": session_id,
            "agentType": session['agentType'],
            "used": used,
            "allocated": total,
            "remaining": total - used,
            "percentUsed": (used / total * 100) if total > 0 else 0,
            "status": session['status']
        }
    
    def release(self, session_id: str):
        """Release budget allocation when session completes."""
        if session_id in self.data['sessions']:
            session = self.data['sessions'][session_id]
            session['status'] = 'completed'
            session['completedAt'] = datetime.now().isoformat()
            
            # Track in usage history
            agent_type = session['agentType']
            if agent_type not in self.data['usage']:
                self.data['usage'][agent_type] = {
                    "totalTokens": 0,
                    "sessionCount": 0
                }
            
            self.data['usage'][agent_type]['totalTokens'] += session['usedTokens']
            self.data['usage'][agent_type]['sessionCount'] += 1
            
            self._save()
            print(f"✓ Released {session_id} (used {session['usedTokens']:,} tokens)")
    
    def get_global_status(self):
        """Get overall budget status."""
        active = [s for s in self.data['sessions'].values() if s['status'] == 'active']
        total_allocated = sum(s['allocatedBudget'] for s in active)
        total_used = sum(s['usedTokens'] for s in active)
        
        return {
            "activeSessions": len(active),
            "totalAllocated": total_allocated,
            "totalUsed": total_used,
            "reservedForMain": self.data['config']['main']['total'],
            "availableForAgents": 200000 - total_allocated
        }

# CLI interface
if __name__ == '__main__':
    import sys
    
    manager = TokenBudgetManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  token-budget-manager.py allocate <session> <type>")
        print("  token-budget-manager.py track <session> <tokens>")
        print("  token-budget-manager.py status [session]")
        print("  token-budget-manager.py release <session>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'allocate':
        session = sys.argv[2]
        agent_type = sys.argv[3] if len(sys.argv) > 3 else "research"
        manager.allocate(session, agent_type)
    
    elif cmd == 'track':
        session = sys.argv[2]
        tokens = int(sys.argv[3])
        manager.track_usage(session, tokens)
    
    elif cmd == 'status':
        if len(sys.argv) > 2:
            # Specific session
            status = manager.get_budget_status(sys.argv[2])
            if status:
                print(json.dumps(status, indent=2))
            else:
                print("Session not found")
        else:
            # Global status
            status = manager.get_global_status()
            print(json.dumps(status, indent=2))
    
    elif cmd == 'release':
        session = sys.argv[2]
        manager.release(session)
