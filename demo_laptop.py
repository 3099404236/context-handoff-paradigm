"""Demo: Laptop Node (Initiator & Handover).
Simulates a laptop starting a long-running troubleshooting task on a remote VPS,
and gracefully suspending/handing off when moving away.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from chp.protocol import PlanStep, TargetEnv
from chp.storage import RelayStorage
from chp.executor import AgentExecutor
from chp.mock_env import MockVPSEnvironment

def run_laptop_session():
    storage = RelayStorage(storage_dir=".chp_relay")
    # Shared remote environment
    shared_vps = MockVPSEnvironment(target_id="vps-prod-01")

    laptop_worker = AgentExecutor(
        device_id="laptop-thinkpad",
        storage=storage,
        target_env_instance=shared_vps
    )

    task_id = "task-vps-502-recovery"
    goal = "排查线上 VPS Nginx 502 错误，定位根本原因并热修服务"

    plan = [
        PlanStep(1, "检查 Nginx 错误日志", "提取上游连接状态与错误码"),
        PlanStep(2, "检查 PHP-FPM 服务状态", "确认守护进程是否存活及退出代码"),
        PlanStep(3, "调整进程池并发配置", "降低 pm.max_children 避免内存超限"),
        PlanStep(4, "重启服务集群", "平滑重载 PHP-FPM 与 Nginx"),
        PlanStep(5, "执行端到端健康校验", "验证 HTTP 接口状态与响应延迟")
    ]

    target_env = TargetEnv(
        env_type="ssh_remote",
        target_id="vps-prod-01",
        connection_params={"host": "185.199.108.153", "auth_profile": "vps_ops_key"},
        working_dir="/var/log"
    )

    print("===============================================================")
    print("💻 [场景 A: 笔记本端] 开始执行长程排障任务...")
    print("===============================================================")

    laptop_worker.initialize_task(
        task_id=task_id,
        goal=goal,
        plan_steps=plan,
        target_env=target_env
    )

    # Execute until step index 2 (i.e. after completing step 1 & 2, pause at step 3)
    # Simulates the user clicking "Handoff to Desktop" before packing laptop
    laptop_worker.run_until_handoff_or_finish(
        task_id=task_id,
        step_delay=0.6,
        pause_at_step=2
    )

    print("💻 [笔记本端] 任务已挂起，电脑可以合盖断网带走了。")

if __name__ == "__main__":
    run_laptop_session()
