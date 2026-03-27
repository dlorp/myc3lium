#!/usr/bin/env python3
"""
OpenClaw Checkpoint Manager
Enables agents to save partial results every 5min, recover on timeout.
"""

import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent
CHECKPOINTS_DIR = MEMORY_DIR / "checkpoints"
CHECKPOINTS_DIR.mkdir(exist_ok=True)

class CheckpointManager:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.checkpoint_file = CHECKPOINTS_DIR / f"{agent_id}.json"
    
    def save(self, progress_percent: int, intermediate_results: dict, next_steps: str = ""):
        """Save checkpoint with current progress."""
        checkpoint = {
            "agentId": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "progressPercent": progress_percent,
            "intermediateResults": intermediate_results,
            "nextSteps": next_steps,
            "status": "in_progress"
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"✓ Checkpoint saved: {progress_percent}% complete")
    
    def load(self):
        """Load latest checkpoint."""
        if not self.checkpoint_file.exists():
            return None
        
        with open(self.checkpoint_file) as f:
            return json.load(f)
    
    def mark_complete(self, final_results: dict):
        """Mark checkpoint as complete."""
        checkpoint = self.load() or {}
        checkpoint.update({
            "timestamp": datetime.now().isoformat(),
            "progressPercent": 100,
            "intermediateResults": final_results,
            "status": "completed"
        })
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def mark_timeout(self):
        """Mark checkpoint as timed out (for recovery)."""
        checkpoint = self.load() or {}
        checkpoint.update({
            "timeoutAt": datetime.now().isoformat(),
            "status": "timeout"
        })
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def cleanup(self):
        """Remove checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

def recover_from_timeout(agent_id: str):
    """Recover partial results from timed-out agent."""
    checkpoint_file = CHECKPOINTS_DIR / f"{agent_id}.json"
    
    if not checkpoint_file.exists():
        return None
    
    with open(checkpoint_file) as f:
        checkpoint = json.load(f)
    
    if checkpoint.get('status') != 'timeout':
        return None
    
    return {
        "recovered": True,
        "progressPercent": checkpoint.get('progressPercent', 0),
        "intermediateResults": checkpoint.get('intermediateResults', {}),
        "nextSteps": checkpoint.get('nextSteps', ''),
        "timeoutAt": checkpoint.get('timeoutAt')
    }

# Example usage
if __name__ == '__main__':
    import sys
    import time
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  checkpoint-manager.py demo                    # Run demo")
        print("  checkpoint-manager.py save <agent> <percent>  # Save checkpoint")
        print("  checkpoint-manager.py load <agent>            # Load checkpoint")
        print("  checkpoint-manager.py recover <agent>         # Recover from timeout")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'demo':
        # Simulate agent with checkpoints
        print("Simulating long-running agent with checkpoints...")
        manager = CheckpointManager("research-agent-123")
        
        # Save checkpoints
        for i in range(0, 100, 20):
            manager.save(
                progress_percent=i,
                intermediate_results={"items_processed": i},
                next_steps=f"Continue from item {i}"
            )
            print(f"  Working... {i}%")
            time.sleep(0.5)
        
        # Simulate timeout at 80%
        print("\n❌ Agent timeout at 80%")
        manager.mark_timeout()
        
        # Recover
        print("\n🔄 Recovering partial results...")
        recovery = recover_from_timeout("research-agent-123")
        if recovery:
            print(f"✓ Recovered {recovery['progressPercent']}% of work")
            print(f"  Intermediate results: {recovery['intermediateResults']}")
            print(f"  Next steps: {recovery['nextSteps']}")
        
        manager.cleanup()
    
    elif cmd == 'save':
        agent = sys.argv[2]
        percent = int(sys.argv[3])
        manager = CheckpointManager(agent)
        manager.save(percent, {"status": "working"}, "Continue processing")
    
    elif cmd == 'load':
        agent = sys.argv[2]
        manager = CheckpointManager(agent)
        checkpoint = manager.load()
        if checkpoint:
            print(json.dumps(checkpoint, indent=2))
        else:
            print("No checkpoint found")
    
    elif cmd == 'recover':
        agent = sys.argv[2]
        recovery = recover_from_timeout(agent)
        if recovery:
            print(json.dumps(recovery, indent=2))
        else:
            print("No recovery data available")
