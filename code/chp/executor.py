"""Breakpoint-Aware Agent Execution Engine (Worker).
Implements the core Context Handoff Paradigm: pause, serialize, transfer, and resume.
"""

import time
from typing import Optional, Callable, Dict, Any
from chp.protocol import (
    ContextBundle,
    TaskStatus,
    TranscriptItem,
    CognitiveState,
    RuntimeCheckpoint,
    TargetEnv,
    PlanStep
)
from chp.storage import RelayStorage
from chp.handover import HandoverGenerator
from chp.mock_env import MockVPSEnvironment


class AgentExecutor:
    """An execution worker on a specific device (e.g., Laptop or Desktop)."""

    def __init__(
        self,
        device_id: str,
        storage: Optional[RelayStorage] = None,
        target_env_instance: Optional[MockVPSEnvironment] = None
    ):
        self.device_id = device_id
        self.storage = storage or RelayStorage()
        self.env = target_env_instance or MockVPSEnvironment()
        self.active_bundle: Optional[ContextBundle] = None
        self._handoff_requested = False

    def request_handoff(self) -> None:
        """Signal the executor to gracefully suspend at the nearest safe boundary."""
        self._handoff_requested = True

    def initialize_task(
        self,
        task_id: str,
        goal: str,
        plan_steps: list[PlanStep],
        target_env: Optional[TargetEnv] = None
    ) -> ContextBundle:
        """Create and register a brand new task."""
        bundle = ContextBundle(
            task_id=task_id,
            status=TaskStatus.PENDING,
            target_env=target_env or TargetEnv(),
            cognitive_state=CognitiveState(
                goal=goal,
                plan=plan_steps,
                working_memory=["任务初始化完成，准备连接远程环境。"]
            ),
            checkpoint=RuntimeCheckpoint(current_step_index=0)
        )
        self.storage.save_bundle(bundle)
        self.active_bundle = bundle
        return bundle

    def run_until_handoff_or_finish(
        self,
        task_id: str,
        step_delay: float = 1.0,
        pause_at_step: Optional[int] = None,
        on_step_callback: Optional[Callable[[PlanStep, ContextBundle], None]] = None
    ) -> ContextBundle:
        """Run task until completed or safely suspended for handoff."""
        # 1. Acquire execution lease
        if not self.storage.acquire_lease(task_id, self.device_id):
            owner = self.storage.get_lease_owner(task_id)
            raise RuntimeError(
                f"[{self.device_id}] 无法获取任务锁！当前任务正在被设备 [{owner}] 执行中。"
            )

        # 2. Load context bundle
        bundle = self.storage.load_bundle(task_id)
        if not bundle:
            self.storage.release_lease(task_id, self.device_id)
            raise ValueError(f"Task {task_id} not found in relay.")

        self.active_bundle = bundle
        self.active_bundle.status = TaskStatus.RUNNING
        self.active_bundle.checkpoint.lease_owner = self.device_id
        self.storage.save_bundle(self.active_bundle)

        print(f"\n=======================================================")
        print(f"🚀 [{self.device_id}] 启动/恢复任务: {bundle.task_id}")
        print(f"🎯 总体目标: {bundle.cognitive_state.goal}")
        print(f"🌐 目标环境: {bundle.target_env.env_type} -> {bundle.target_env.target_id}")

        if bundle.handover_note:
            print(f"\n📋 [检测到前置交接便签]:")
            print(f"   交接自: {bundle.handover_note.from_device}")
            print(f"   摘要: {bundle.handover_note.summary}")
            print(f"   建议下一步: {bundle.handover_note.recommended_next_step}")
            if bundle.handover_note.key_findings:
                print(f"   已掌握事实:")
                for f in bundle.handover_note.key_findings:
                    print(f"     • {f}")
        print(f"=======================================================\n")

        plan = self.active_bundle.cognitive_state.plan
        start_idx = self.active_bundle.checkpoint.current_step_index

        try:
            for idx in range(start_idx, len(plan)):
                step = plan[idx]
                self.active_bundle.checkpoint.current_step_index = idx

                # Check if simulated or external handoff is requested before executing step
                if self._handoff_requested or (pause_at_step is not None and idx == pause_at_step):
                    print(f"\n⏸️  [{self.device_id}] 收到转移请求 (Handoff Triggered)！正在生成上下文切片...")
                    self._perform_suspend_and_handoff()
                    return self.active_bundle

                step.status = "in_progress"
                print(f"▶️  [{self.device_id}] 执行第 {step.step_id}/{len(plan)} 步: {step.title}")

                # Execute mock step
                self._execute_step_logic(step)

                step.status = "done"
                time.sleep(step_delay)

                if on_step_callback:
                    on_step_callback(step, self.active_bundle)

                # Persist intermediate checkpoint
                self.storage.save_bundle(self.active_bundle)

            # All steps completed
            self.active_bundle.status = TaskStatus.COMPLETED
            self.active_bundle.cognitive_state.working_memory.append("所有诊断与修复步骤已成功通过验证。")
            self.storage.save_bundle(self.active_bundle)
            print(f"\n🎉 [{self.device_id}] 任务全部执行完成！线上服务已恢复。")
            return self.active_bundle

        finally:
            self.storage.release_lease(task_id, self.device_id)

    def _execute_step_logic(self, step: PlanStep) -> None:
        """Domain-specific logic for mock VPS troubleshooting."""
        state = self.active_bundle.cognitive_state
        cp = self.active_bundle.checkpoint

        if step.step_id == 1:
            code, out = self.env.execute("tail -n 20 /var/log/nginx/error.log")
            state.transcript.append(TranscriptItem(time.time(), "tool", "ssh_exec", out))
            state.working_memory.append("发现 Nginx error.log 大量 111 Connection refused (9000端口拒绝连接)")
            step.result_summary = "确认上游 FastCGI (php-fpm) 服务无响应"
            cp.variables["upstream_port"] = 9000

        elif step.step_id == 2:
            code, out = self.env.execute("systemctl status php-fpm")
            state.transcript.append(TranscriptItem(time.time(), "tool", "ssh_exec", out))
            state.working_memory.append("定位故障根因: php-fpm 服务崩溃，原因为 'oom-kill' (系统内存溢出杀除)")
            step.result_summary = "PHP-FPM 进程因 OOM 被 Linux 内核强制杀死"
            cp.variables["root_cause"] = "OOM-Killed"

        elif step.step_id == 3:
            code, out = self.env.execute("grep -E 'pm.max_children' /etc/php-fpm.d/www.conf")
            state.transcript.append(TranscriptItem(time.time(), "tool", "ssh_exec", out))
            state.working_memory.append("发现配置问题: pm.max_children 被设为 250，远超机器内存承载力")
            # Apply fix
            c2, o2 = self.env.execute("sed -i 's/pm.max_children = 250/pm.max_children = 50/' /etc/php-fpm.d/www.conf")
            state.transcript.append(TranscriptItem(time.time(), "tool", "ssh_exec", o2))
            step.result_summary = "完成配置热修: pm.max_children 从 250 下调至 50"
            cp.variables["fixed_max_children"] = 50

        elif step.step_id == 4:
            code, out = self.env.execute("systemctl restart php-fpm && systemctl reload nginx")
            state.transcript.append(TranscriptItem(time.time(), "tool", "ssh_exec", out))
            state.working_memory.append("服务重启成功，当前内存占用稳定在 380MB")
            step.result_summary = "PHP-FPM 与 Nginx 重启成功"

        elif step.step_id == 5:
            code, out = self.env.execute("curl -I http://localhost/healthz")
            state.transcript.append(TranscriptItem(time.time(), "tool", "ssh_exec", out))
            state.working_memory.append("健康检查通过: HTTP 200 OK，响应时间 < 20ms")
            step.result_summary = "线上验证通过，服务已恢复健康状态"

        print(f"   ↳ 结果: {step.result_summary}")

    def _perform_suspend_and_handoff(self) -> None:
        """Create snapshot, generate note, and suspend."""
        self.active_bundle.status = TaskStatus.SUSPENDED_FOR_HANDOFF
        note = HandoverGenerator.generate(
            from_device=self.device_id,
            cognitive_state=self.active_bundle.cognitive_state,
            checkpoint=self.active_bundle.checkpoint,
            to_target="any_worker"
        )
        self.active_bundle.handover_note = note
        self.storage.save_bundle(self.active_bundle)
        print(f"📦 [Handoff 完成] 上下文已打包存储至中继。")
        print(f"   • 当前断点步骤: 第 {self.active_bundle.checkpoint.current_step_index + 1} 步")
        print(f"   • 包含事实项数: {len(self.active_bundle.cognitive_state.working_memory)} 条")
        print(f"   • 设备 [{self.device_id}] 已安全释放锁，随时可由其他终端接管！\n")
