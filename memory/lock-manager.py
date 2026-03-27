#!/usr/bin/env python3
"""
OpenClaw Resource Lock Manager
Prevents concurrent writes to shared resources (files, APIs).
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

LOCKS_FILE = Path(__file__).parent / "resource-locks.json"

class LockManager:
    def __init__(self):
        self.locks_file = LOCKS_FILE
        self._load()
    
    def _load(self):
        """Load locks from file."""
        with open(self.locks_file) as f:
            self.data = json.load(f)
    
    def _save(self):
        """Save locks to file."""
        with open(self.locks_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _cleanup_expired(self):
        """Remove expired locks."""
        now = datetime.now().isoformat()
        
        for resource_name, resource_data in self.data['resources'].items():
            lock = resource_data.get('currentLock')
            if lock and lock.get('expiresAt', '') < now:
                resource_data['currentLock'] = None
                print(f"  Released expired lock on {resource_name}")
        
        # Remove expired locks from active locks dict
        expired = [k for k, v in self.data['locks'].items() if v.get('expiresAt', '') < now]
        for lock_id in expired:
            del self.data['locks'][lock_id]
    
    def acquire(self, resource: str, session_id: str, agent_id: str, purpose: str = "", timeout_seconds: int = 300) -> bool:
        """
        Attempt to acquire lock on resource.
        Returns True if acquired, False if already locked.
        """
        self._load()
        self._cleanup_expired()
        
        if resource not in self.data['resources']:
            print(f"Warning: Unknown resource '{resource}', allowing by default")
            return True
        
        resource_data = self.data['resources'][resource]
        
        # Check if resource allows this session
        allowed_sessions = resource_data.get('allowedSessions', [])
        if allowed_sessions and session_id not in allowed_sessions:
            print(f"Error: Session '{session_id}' not allowed to access {resource}")
            return False
        
        # Check if already locked
        current_lock = resource_data.get('currentLock')
        if current_lock:
            if current_lock['sessionId'] == session_id:
                print(f"  Re-acquired lock on {resource} (same session)")
                return True
            else:
                print(f"  Lock unavailable: {resource} locked by {current_lock['agentId']}")
                return False
        
        # Acquire lock
        now = datetime.now()
        expires = now + timedelta(seconds=timeout_seconds)
        
        lock = {
            'resource': resource,
            'sessionId': session_id,
            'agentId': agent_id,
            'acquiredAt': now.isoformat(),
            'expiresAt': expires.isoformat(),
            'purpose': purpose
        }
        
        lock_id = f"{resource}:{session_id}:{int(time.time())}"
        
        self.data['locks'][lock_id] = lock
        self.data['resources'][resource]['currentLock'] = lock
        
        self._save()
        print(f"✓ Acquired lock: {resource} (expires in {timeout_seconds}s)")
        return True
    
    def release(self, resource: str, session_id: str):
        """Release lock on resource."""
        self._load()
        
        if resource not in self.data['resources']:
            return
        
        resource_data = self.data['resources'][resource]
        current_lock = resource_data.get('currentLock')
        
        if not current_lock:
            print(f"  No lock to release: {resource}")
            return
        
        if current_lock['sessionId'] != session_id:
            print(f"  Cannot release: {resource} locked by different session")
            return
        
        # Remove lock
        resource_data['currentLock'] = None
        
        # Remove from locks dict
        lock_id = next((k for k, v in self.data['locks'].items() 
                       if v['resource'] == resource and v['sessionId'] == session_id), None)
        if lock_id:
            del self.data['locks'][lock_id]
        
        self._save()
        print(f"✓ Released lock: {resource}")
    
    def status(self):
        """Show current lock status."""
        self._load()
        self._cleanup_expired()
        
        locked = [k for k, v in self.data['resources'].items() if v.get('currentLock')]
        available = [k for k, v in self.data['resources'].items() if not v.get('currentLock')]
        
        print(f"Resource Lock Status")
        print("=" * 50)
        print(f"Locked: {len(locked)}")
        for resource in locked:
            lock = self.data['resources'][resource]['currentLock']
            print(f"  {resource} → {lock['agentId']} ({lock['purpose']})")
        
        print(f"\nAvailable: {len(available)}")
        if len(available) <= 10:
            for resource in available:
                print(f"  {resource}")
        else:
            print(f"  ({available[:5]}...)")
        
        print()

# CLI interface
if __name__ == '__main__':
    import sys
    
    manager = LockManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  lock-manager.py status")
        print("  lock-manager.py acquire <resource> <session> <agent> [purpose]")
        print("  lock-manager.py release <resource> <session>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'status':
        manager.status()
    elif cmd == 'acquire':
        if len(sys.argv) < 5:
            print("Usage: lock-manager.py acquire <resource> <session> <agent> [purpose]")
            sys.exit(1)
        resource = sys.argv[2]
        session = sys.argv[3]
        agent = sys.argv[4]
        purpose = sys.argv[5] if len(sys.argv) > 5 else ""
        
        success = manager.acquire(resource, session, agent, purpose)
        sys.exit(0 if success else 1)
    elif cmd == 'release':
        if len(sys.argv) < 4:
            print("Usage: lock-manager.py release <resource> <session>")
            sys.exit(1)
        resource = sys.argv[2]
        session = sys.argv[3]
        manager.release(resource, session)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
