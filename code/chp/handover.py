"""Handover Note & Semantic Context Summarizer.
Generates human- and agent-readable transition digests when pausing/transferring tasks.
"""

import time
from typing import List
from chp.protocol import CognitiveState, HandoverNote, RuntimeCheckpoint


class HandoverGenerator:
    """Extracts high-level handover notes from cognitive states."""

    @staticmethod
    def generate(
        from_device: str,
        cognitive_state: CognitiveState,
        checkpoint: RuntimeCheckpoint,
        to_target: str = "any_worker"
    ) -> HandoverNote:
        """Synthesize a structured handover note based on current execution progress."""
        completed_steps = [s for s in cognitive_state.plan if s.status == "done"]
        in_progress_step = next((s for s in cognitive_state.plan if s.status == "in_progress"), None)
        pending_steps = [s for s in cognitive_state.plan if s.status == "todo"]

        summary = (
            f"任务「{cognitive_state.goal}」已由节点 [{from_device}] 执行至阶段 {checkpoint.current_step_index + 1}/"
            f"{len(cognitive_state.plan)}。现已安全挂起并生成上下文切片。"
        )

        key_findings: List[str] = list(cognitive_state.working_memory)

        if in_progress_step:
            recommended_next = (
                f"继续执行第 {in_progress_step.step_id} 步: [{in_progress_step.title}]。环境断点已锁定。"
            )
        elif pending_steps:
            recommended_next = (
                f"继续执行第 {pending_steps[0].step_id} 步: [{pending_steps[0].title}]。"
            )
        else:
            recommended_next = "所有既定步骤已完成，请执行最终交付校验。"

        return HandoverNote(
            created_at=time.time(),
            from_device=from_device,
            to_target=to_target,
            summary=summary,
            key_findings=key_findings,
            recommended_next_step=recommended_next
        )
