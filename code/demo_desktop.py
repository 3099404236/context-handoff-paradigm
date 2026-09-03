"""Demo: Desktop Node (Receiver & Continuation).
Simulates a desktop workstation detecting suspended tasks in the relay,
inspecting the handover note, resuming execution, and finishing the job.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from chp.protocol import TaskStatus
from chp.storage import RelayStorage
from chp.executor import AgentExecutor
from chp.mock_env import MockVPSEnvironment

def run_desktop_session():
    storage = RelayStorage(storage_dir=".chp_relay")
    # Shared remote environment (or re-connected via SSH)
    shared_vps = MockVPSEnvironment(target_id="vps-prod-01")

    desktop_worker = AgentExecutor(
        device_id="desktop-workstation",
        storage=storage,
        target_env_instance=shared_vps
    )

    print("===============================================================")
    print("🖥️  [场景 B: 台式机端] 启动，正在扫描是否有挂起或待交接任务...")
    print("===============================================================")

    # Scan for tasks awaiting handoff
    pending_handoffs = storage.list_bundles(status=TaskStatus.SUSPENDED_FOR_HANDOFF)

    if not pending_handoffs:
        print("未检测到待交接任务。")
        return

    target_task = pending_handoffs[0]
    print(f"✨ 发现待接管任务: [{target_task.task_id}]")
    print(f"   原发起节点: {target_task.handover_note.from_device if target_task.handover_note else 'Unknown'}")
    print(f"   目标: {target_task.cognitive_state.goal}")
    print(f"   当前进度: 第 {target_task.checkpoint.current_step_index + 1} 步")
    print("---------------------------------------------------------------")
    print("🖥️  [台式机端] 正在一键接管 (Resume)...")

    # Resume without pausing, running till finish
    desktop_worker.run_until_handoff_or_finish(
        task_id=target_task.task_id,
        step_delay=0.6,
        pause_at_step=None
    )

    print("🖥️  [台式机端] 任务已全部成功完成，接力闭环成功！")

if __name__ == "__main__":
    run_desktop_session()
