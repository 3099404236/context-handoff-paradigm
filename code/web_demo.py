"""Zero-dependency Interactive Web Dashboard for Context Handoff Paradigm.
Uses standard Python http.server to provide a visual two-device handoff experience.
"""

import http.server
import socketserver
import json
import urllib.parse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from chp.protocol import PlanStep, TargetEnv, TaskStatus
from chp.storage import RelayStorage
from chp.executor import AgentExecutor
from chp.mock_env import MockVPSEnvironment

PORT = 8765
STORAGE_DIR = ".chp_relay"

# Global runtime state for demo
storage = RelayStorage(storage_dir=STORAGE_DIR)
shared_vps = MockVPSEnvironment(target_id="vps-prod-01")
laptop_worker = AgentExecutor("laptop-thinkpad", storage, shared_vps)
desktop_worker = AgentExecutor("desktop-workstation", storage, shared_vps)

DEFAULT_TASK_ID = "task-vps-502-recovery"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>上下文转移范式 (Context Handoff Paradigm) - 双设备接力控制台</title>
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --border: #334155;
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --primary: #38bdf8;
            --accent: #818cf8;
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 24px;
        }
        .header {
            text-align: center;
            margin-bottom: 24px;
        }
        .header h1 {
            font-size: 26px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .header p { color: var(--text-dim); font-size: 14px; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 340px 1fr;
            gap: 20px;
        }
        @media (max-width: 1100px) {
            .grid { grid-template-columns: 1fr; }
        }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }
        .device-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 15px;
            font-weight: 600;
        }
        .status-tag {
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 9999px;
            background: #334155;
            color: #cbd5e1;
        }
        .btn {
            background: var(--primary);
            color: #0f172a;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
        .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
        .btn-warning { background: var(--warning); }
        .btn-success { background: var(--success); }
        .step-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .step-item {
            padding: 10px 12px;
            border-radius: 8px;
            background: #0f172a;
            border-left: 4px solid var(--border);
            font-size: 13px;
        }
        .step-item.done { border-left-color: var(--success); }
        .step-item.in_progress { border-left-color: var(--warning); background: #1e1b4b; }
        .step-title { font-weight: 600; margin-bottom: 2px; }
        .step-desc { font-size: 12px; color: var(--text-dim); }
        .step-res { font-size: 12px; color: var(--success); margin-top: 4px; }
        
        .relay-card {
            background: #111827;
            border-color: #374151;
        }
        .note-box {
            background: #182234;
            border: 1px dashed var(--accent);
            border-radius: 8px;
            padding: 14px;
            font-size: 13px;
            line-height: 1.5;
        }
        .note-title {
            color: var(--accent);
            font-weight: 600;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .fact-item {
            margin-left: 16px;
            font-size: 12px;
            color: #cbd5e1;
        }
        .logs {
            background: #090d16;
            border-radius: 8px;
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            height: 140px;
            overflow-y: auto;
            color: #a5f3fc;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>上下文转移范式 (Context Handoff Paradigm)</h1>
        <p>长程 Agent 任务跨设备认知无缝接力 • 状态与环境解耦原型</p>
    </div>

    <div class="grid">
        <!-- 笔记本面板 -->
        <div class="card">
            <div class="card-header">
                <div class="device-badge">💻 节点 A: 笔记本 (ThinkPad)</div>
                <span id="laptop-status" class="status-tag">空闲</span>
            </div>
            <div>
                <p style="font-size: 13px; color: var(--text-dim); margin-bottom: 8px;">
                    目标: 远程排查 VPS 502 并热修服务
                </p>
                <div style="display: flex; gap: 8px;">
                    <button id="btn-laptop-start" class="btn" onclick="laptopStart()">
                        🚀 发起任务 (执行前2步)
                    </button>
                    <button id="btn-laptop-handoff" class="btn btn-warning" onclick="laptopHandoff()" disabled>
                        ⏸️ 一键转交 (Handoff)
                    </button>
                </div>
            </div>
            <div class="step-list" id="laptop-steps">
                <!-- 动态填充 -->
            </div>
            <div class="logs" id="laptop-logs">等待任务启动...</div>
        </div>

        <!-- 中继状态面板 -->
        <div class="card relay-card">
            <div class="card-header">
                <div class="device-badge" style="color: var(--accent);">📦 上下文状态中枢 (Relay)</div>
                <span id="lock-status" class="status-tag">无持锁者</span>
            </div>
            <div class="note-box" id="handover-card">
                <div class="note-title">📋 交接便签 (Handover Note)</div>
                <div id="note-content" style="color: var(--text-dim);">
                    暂无挂起的交接切片。当笔记本发起转移时，将自动在此捕获高层认知摘要与断点。
                </div>
            </div>
            <div style="font-size: 12px; color: var(--text-dim);">
                <div><strong>目标环境:</strong> <span id="relay-env">vps-prod-01 (SSH)</span></div>
                <div><strong>断点游标:</strong> <span id="relay-step">-</span></div>
                <div><strong>任务状态:</strong> <span id="relay-status">未初始化</span></div>
            </div>
            <button class="btn" style="background:#334155; color:#f8fafc;" onclick="refreshState()">
                🔄 刷新状态
            </button>
        </div>

        <!-- 台式机面板 -->
        <div class="card">
            <div class="card-header">
                <div class="device-badge">🖥️ 节点 B: 台式机 (Workstation)</div>
                <span id="desktop-status" class="status-tag">待命中</span>
            </div>
            <div>
                <p style="font-size: 13px; color: var(--text-dim); margin-bottom: 8px;">
                    接收笔记本暂存的任务切片，直接恢复断点续跑
                </p>
                <button id="btn-desktop-resume" class="btn btn-success" onclick="desktopResume()" disabled>
                    ✨ 一键接管并完成 (Resume)
                </button>
            </div>
            <div class="step-list" id="desktop-steps">
                <!-- 动态填充 -->
            </div>
            <div class="logs" id="desktop-logs">台式机准备就绪，等待接管...</div>
        </div>
    </div>

    <script>
        async function fetchState() {
            const res = await fetch('/api/state');
            return await res.json();
        }

        function renderSteps(steps, containerId, activeDevice) {
            const el = document.getElementById(containerId);
            if (!steps || steps.length === 0) {
                el.innerHTML = '<div style="color:#64748b; font-size:12px;">暂无计划步骤</div>';
                return;
            }
            el.innerHTML = steps.map(s => `
                <div class="step-item ${s.status}">
                    <div class="step-title">第 ${s.step_id} 步: ${s.title} (${s.status})</div>
                    <div class="step-desc">${s.description}</div>
                    ${s.result_summary ? `<div class="step-res">✓ ${s.result_summary}</div>` : ''}
                </div>
            `).join('');
        }

        async function refreshState() {
            const data = await fetchState();
            const b = data.bundle;

            if (b) {
                document.getElementById('relay-env').innerText = `${b.target_env.env_type} -> ${b.target_env.target_id}`;
                document.getElementById('relay-step').innerText = `Step ${b.checkpoint.current_step_index + 1}/${b.cognitive_state.plan.length}`;
                document.getElementById('relay-status').innerText = b.status;

                renderSteps(b.cognitive_state.plan, 'laptop-steps', 'laptop');
                renderSteps(b.cognitive_state.plan, 'desktop-steps', 'desktop');

                if (b.handover_note) {
                    const n = b.handover_note;
                    document.getElementById('handover-card').innerHTML = `
                        <div class="note-title">📋 交接便签 (Handover Note)</div>
                        <p style="margin-bottom:6px; color:#e2e8f0;"><strong>摘要:</strong> ${n.summary}</p>
                        <p style="margin-bottom:6px; color:#38bdf8;"><strong>建议下一步:</strong> ${n.recommended_next_step}</p>
                        <div style="font-weight:600; font-size:12px; margin-top:8px;">已锁定关键事实:</div>
                        ${n.key_findings.map(f => `<div class="fact-item">• ${f}</div>`).join('')}
                    `;
                }

                // Controls
                if (b.status === 'suspended_for_handoff') {
                    document.getElementById('btn-desktop-resume').disabled = false;
                    document.getElementById('btn-laptop-handoff').disabled = true;
                    document.getElementById('laptop-status').innerText = '已挂起/合盖';
                    document.getElementById('desktop-status').innerText = '可接管';
                } else if (b.status === 'completed') {
                    document.getElementById('btn-desktop-resume').disabled = true;
                    document.getElementById('btn-laptop-handoff').disabled = true;
                    document.getElementById('laptop-status').innerText = '任务完成';
                    document.getElementById('desktop-status').innerText = '完成交付';
                }
            }
            if (data.lease_owner) {
                document.getElementById('lock-status').innerText = `持锁: ${data.lease_owner}`;
            } else {
                document.getElementById('lock-status').innerText = '无持锁 (已释放)';
            }
        }

        async function laptopStart() {
            document.getElementById('laptop-logs').innerText += "\\n[笔记本] 启动排障流程...";
            document.getElementById('btn-laptop-start').disabled = true;
            document.getElementById('laptop-status').innerText = '执行中';
            await fetch('/api/laptop/start', {method: 'POST'});
            document.getElementById('btn-laptop-handoff').disabled = false;
            await refreshState();
        }

        async function laptopHandoff() {
            document.getElementById('laptop-logs').innerText += "\\n[笔记本] 触发一键转交 (Handoff)... 状态已暂存至中继。合盖断网。";
            await fetch('/api/laptop/handoff', {method: 'POST'});
            await refreshState();
        }

        async function desktopResume() {
            document.getElementById('desktop-logs').innerText += "\\n[台式机] 读取交接便签，恢复环境并接管 Step 3...";
            document.getElementById('btn-desktop-resume').disabled = true;
            document.getElementById('desktop-status').innerText = '接管执行中';
            await fetch('/api/desktop/resume', {method: 'POST'});
            document.getElementById('desktop-logs').innerText += "\\n[台式机] 全部步骤执行完毕，生产服务正常！";
            await refreshState();
        }

        setInterval(refreshState, 2000);
        refreshState();
    </script>
</body>
</html>
"""


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/state":
            bundle = storage.load_bundle(DEFAULT_TASK_ID)
            owner = storage.get_lease_owner(DEFAULT_TASK_ID)
            data = {
                "bundle": bundle.to_dict() if bundle else None,
                "lease_owner": owner
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/laptop/start":
            # Initialize and run step 1 & 2
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
                connection_params={"host": "185.199.108.153"},
                working_dir="/var/log"
            )
            laptop_worker.initialize_task(
                task_id=DEFAULT_TASK_ID,
                goal="排查线上 VPS Nginx 502 错误并热修",
                plan_steps=plan,
                target_env=target_env
            )
            # Run first 2 steps
            laptop_worker.run_until_handoff_or_finish(
                DEFAULT_TASK_ID, step_delay=0.2, pause_at_step=2
            )
            self._respond_json({"ok": True})

        elif parsed.path == "/api/laptop/handoff":
            # Explicit handoff trigger
            laptop_worker.request_handoff()
            self._respond_json({"ok": True})

        elif parsed.path == "/api/desktop/resume":
            # Desktop resumes remaining steps
            desktop_worker.run_until_handoff_or_finish(
                DEFAULT_TASK_ID, step_delay=0.2, pause_at_step=None
            )
            self._respond_json({"ok": True})

        else:
            self.send_response(404)
            self.end_headers()

    def _respond_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def main():
    socketserver.TCPServer.allow_reuse_address = True
    print(f"CHP Web Dashboard starting on port {PORT}...", flush=True)
    with socketserver.TCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"CHP Web Dashboard running at http://127.0.0.1:{PORT}", flush=True)
        httpd.serve_forever()



if __name__ == "__main__":
    main()
