"""State Storage & Relay Engine with Distributed Lease Locking.
Provides persistent storage and coordination for context handoff between workers.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Optional
from chp.protocol import ContextBundle, TaskStatus


class RelayStorage:
    """Abstract/File-based Relay Storage for Context Bundles."""

    def __init__(self, storage_dir: str = ".chp_relay"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.locks_dir = self.storage_dir / "locks"
        self.locks_dir.mkdir(parents=True, exist_ok=True)

    def _get_bundle_path(self, task_id: str) -> Path:
        return self.storage_dir / f"{task_id}.bundle.json"

    def _get_lock_path(self, task_id: str) -> Path:
        return self.locks_dir / f"{task_id}.lock"

    def save_bundle(self, bundle: ContextBundle) -> None:
        """Persist or update context bundle in relay."""
        bundle.updated_at = time.time()
        bundle_path = self._get_bundle_path(bundle.task_id)
        temp_path = bundle_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(bundle.to_json(indent=2))
        # Atomic replace
        os.replace(temp_path, bundle_path)

    def load_bundle(self, task_id: str) -> Optional[ContextBundle]:
        """Load a context bundle by task ID."""
        bundle_path = self._get_bundle_path(task_id)
        if not bundle_path.exists():
            return None
        try:
            with open(bundle_path, "r", encoding="utf-8") as f:
                return ContextBundle.from_json(f.read())
        except Exception as e:
            print(f"[RelayStorage] Error loading {task_id}: {e}")
            return None

    def list_bundles(self, status: Optional[TaskStatus] = None) -> List[ContextBundle]:
        """List all available context bundles, optionally filtered by status."""
        bundles = []
        for file in self.storage_dir.glob("*.bundle.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    bundle = ContextBundle.from_json(f.read())
                    if status is None or bundle.status == status:
                        bundles.append(bundle)
            except Exception:
                continue
        bundles.sort(key=lambda b: b.updated_at, reverse=True)
        return bundles

    def acquire_lease(self, task_id: str, device_id: str, ttl_seconds: float = 30.0) -> bool:
        """Attempt to acquire execution lease lock for a task."""
        lock_file = self._get_lock_path(task_id)
        now = time.time()

        if lock_file.exists():
            try:
                with open(lock_file, "r", encoding="utf-8") as f:
                    lock_data = json.loads(f.read())
                owner = lock_data.get("owner")
                expire_at = lock_data.get("expire_at", 0)

                # Lease is still valid and owned by someone else
                if owner != device_id and now < expire_at:
                    return False
            except Exception:
                pass  # corrupted lock, allow overwrite

        # Write new lock
        lock_info = {
            "task_id": task_id,
            "owner": device_id,
            "acquired_at": now,
            "expire_at": now + ttl_seconds
        }
        try:
            with open(lock_file, "w", encoding="utf-8") as f:
                json.dump(lock_info, f)
            return True
        except Exception:
            return False

    def release_lease(self, task_id: str, device_id: str) -> bool:
        """Release execution lease lock."""
        lock_file = self._get_lock_path(task_id)
        if not lock_file.exists():
            return True

        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                lock_data = json.loads(f.read())
            if lock_data.get("owner") == device_id:
                lock_file.unlink(missing_ok=True)
                return True
            return False
        except Exception:
            lock_file.unlink(missing_ok=True)
            return True

    def get_lease_owner(self, task_id: str) -> Optional[str]:
        """Check who currently holds the lease."""
        lock_file = self._get_lock_path(task_id)
        if not lock_file.exists():
            return None
        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                lock_data = json.loads(f.read())
            if time.time() < lock_data.get("expire_at", 0):
                return lock_data.get("owner")
        except Exception:
            pass
        return None
