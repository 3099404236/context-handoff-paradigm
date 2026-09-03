"""Unit and Integration Tests for Context Handoff Paradigm (CHP).
Tests serialization, lease locking, handoff, and resume capabilities.
"""

import os
import sys
import shutil
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from chp.protocol import (
    ContextBundle,
    TaskStatus,
    PlanStep,
    TargetEnv,
    CognitiveState,
    RuntimeCheckpoint
)
from chp.storage import RelayStorage
from chp.executor import AgentExecutor
from chp.mock_env import MockVPSEnvironment


class TestContextHandoff(unittest.TestCase):

    def setUp(self):
        self.test_relay_dir = ".test_relay"
        self.storage = RelayStorage(storage_dir=self.test_relay_dir)

    def tearDown(self):
        if Path(self.test_relay_dir).exists():
            shutil.rmtree(self.test_relay_dir, ignore_errors=True)

    def test_bundle_serialization(self):
        """Ensure ContextBundle serializes and deserializes losslessly."""
        bundle = ContextBundle(
            task_id="test-task-01",
            status=TaskStatus.RUNNING,
            target_env=TargetEnv(env_type="vps", target_id="vps-99"),
            cognitive_state=CognitiveState(
                goal="Fix nginx issue",
                plan=[PlanStep(1, "Check logs", "tail logs", "done")],
                working_memory=["Fact 1: upstream down"]
            ),
            checkpoint=RuntimeCheckpoint(current_step_index=1, variables={"foo": "bar"})
        )

        json_str = bundle.to_json()
        restored = ContextBundle.from_json(json_str)

        self.assertEqual(restored.task_id, "test-task-01")
        self.assertEqual(restored.status, TaskStatus.RUNNING)
        self.assertEqual(restored.target_env.target_id, "vps-99")
        self.assertEqual(len(restored.cognitive_state.plan), 1)
        self.assertEqual(restored.cognitive_state.plan[0].title, "Check logs")
        self.assertEqual(restored.checkpoint.variables["foo"], "bar")

    def test_lease_lock_mutual_exclusion(self):
        """Ensure two devices cannot execute the same task concurrently."""
        task_id = "test-task-lock"
        bundle = ContextBundle(task_id=task_id, status=TaskStatus.PENDING)
        self.storage.save_bundle(bundle)

        # Device A acquires lock
        acquired_a = self.storage.acquire_lease(task_id, "device-a", ttl_seconds=5)
        self.assertTrue(acquired_a)

        # Device B should fail to acquire
        acquired_b = self.storage.acquire_lease(task_id, "device-b", ttl_seconds=5)
        self.assertFalse(acquired_b)

        # Device A releases lock
        self.storage.release_lease(task_id, "device-a")

        # Now Device B can acquire
        acquired_b_again = self.storage.acquire_lease(task_id, "device-b", ttl_seconds=5)
        self.assertTrue(acquired_b_again)
        self.storage.release_lease(task_id, "device-b")

    def test_handoff_and_resume_pipeline(self):
        """End-to-end test of worker handoff and resume."""
        task_id = "test-handoff-pipeline"
        shared_env = MockVPSEnvironment(target_id="vps-prod-01")

        laptop = AgentExecutor("laptop", self.storage, shared_env)
        desktop = AgentExecutor("desktop", self.storage, shared_env)

        plan = [
            PlanStep(1, "Step 1", "Desc 1"),
            PlanStep(2, "Step 2", "Desc 2"),
            PlanStep(3, "Step 3", "Desc 3"),
            PlanStep(4, "Step 4", "Desc 4"),
            PlanStep(5, "Step 5", "Desc 5")
        ]

        laptop.initialize_task(
            task_id=task_id,
            goal="Test Handoff",
            plan_steps=plan
        )

        # Laptop executes until step 2 (index 2 pause)
        laptop_bundle = laptop.run_until_handoff_or_finish(task_id, step_delay=0.01, pause_at_step=2)
        self.assertEqual(laptop_bundle.status, TaskStatus.SUSPENDED_FOR_HANDOFF)
        self.assertEqual(laptop_bundle.checkpoint.current_step_index, 2)
        self.assertIsNotNone(laptop_bundle.handover_note)
        self.assertEqual(laptop_bundle.handover_note.from_device, "laptop")

        # Desktop takes over and finishes remaining steps
        desktop_bundle = desktop.run_until_handoff_or_finish(task_id, step_delay=0.01)
        self.assertEqual(desktop_bundle.status, TaskStatus.COMPLETED)
        self.assertEqual(all(s.status == "done" for s in desktop_bundle.cognitive_state.plan), True)


if __name__ == "__main__":
    unittest.main()
