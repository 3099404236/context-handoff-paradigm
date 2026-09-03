"""Context Handoff Protocol (CHP) Data Models.
Defines serialization format for Agent Cognitive & Execution State.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import time
from typing import List, Dict, Any, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUSPENDED_FOR_HANDOFF = "suspended_for_handoff"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TargetEnv:
    """Specification of the target environment (decoupled from local machine)."""
    env_type: str = "ssh_remote"                # ssh_remote, cloud_api, docker, vps
    target_id: str = "vps-prod-01"              # Logical identifier of the remote environment
    connection_params: Dict[str, Any] = field(default_factory=dict)
    working_dir: str = "/var/log/nginx"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetEnv':
        return cls(**data)


@dataclass
class PlanStep:
    """Individual step in the structured task plan."""
    step_id: int
    title: str
    description: str
    status: str = "todo"                        # todo, in_progress, done, failed
    result_summary: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanStep':
        return cls(**data)


@dataclass
class TranscriptItem:
    """Interaction or tool execution record."""
    timestamp: float
    role: str                                   # system, agent, tool, observation
    action: str                                 # e.g., 'ssh_exec', 'diagnose', 'patch_config'
    content: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptItem':
        return cls(**data)


@dataclass
class CognitiveState:
    """Cognitive context of the agent (goals, plans, working memory)."""
    goal: str
    plan: List[PlanStep] = field(default_factory=list)
    working_memory: List[str] = field(default_factory=list)
    transcript: List[TranscriptItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitiveState':
        plan = [PlanStep.from_dict(p) for p in data.get("plan", [])]
        transcript = [TranscriptItem.from_dict(t) for t in data.get("transcript", [])]
        return cls(
            goal=data.get("goal", ""),
            plan=plan,
            working_memory=data.get("working_memory", []),
            transcript=transcript
        )


@dataclass
class RuntimeCheckpoint:
    """Runtime execution position and intermediate variables."""
    current_step_index: int = 0
    variables: Dict[str, Any] = field(default_factory=dict)
    lease_owner: Optional[str] = None          # Device holding active execution lock
    lease_expire_at: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuntimeCheckpoint':
        return cls(**data)


@dataclass
class HandoverNote:
    """Human- and Agent-readable summary for handoff."""
    created_at: float = field(default_factory=time.time)
    from_device: str = "unknown"
    to_target: str = "any_worker"
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommended_next_step: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HandoverNote':
        return cls(**data)


@dataclass
class ContextBundle:
    """The complete transferable Context Snapshot."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    target_env: TargetEnv = field(default_factory=TargetEnv)
    cognitive_state: CognitiveState = field(default_factory=lambda: CognitiveState(goal=""))
    checkpoint: RuntimeCheckpoint = field(default_factory=RuntimeCheckpoint)
    handover_note: Optional[HandoverNote] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value if isinstance(self.status, TaskStatus) else self.status
        return data

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextBundle':
        status = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        target_env = TargetEnv.from_dict(data.get("target_env", {}))
        cognitive_state = CognitiveState.from_dict(data.get("cognitive_state", {}))
        checkpoint = RuntimeCheckpoint.from_dict(data.get("checkpoint", {}))
        handover_note = None
        if data.get("handover_note"):
            handover_note = HandoverNote.from_dict(data["handover_note"])

        return cls(
            task_id=data["task_id"],
            status=status,
            target_env=target_env,
            cognitive_state=cognitive_state,
            checkpoint=checkpoint,
            handover_note=handover_note,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ContextBundle':
        return cls.from_dict(json.loads(json_str))
