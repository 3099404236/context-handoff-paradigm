# 面向长程自主智能体的上下文转移范式与解耦架构研究
(Context Handoff Paradigm, CHP)

> **Decoupling Cognitive State, Target Environment, and Execution Nodes for Long-Running Autonomous Agents**

[![Paper](https://img.shields.io/badge/Paper-main.pdf-red.svg)](paper/main.pdf)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](code/)

---

## 1. 项目简介与核心动机

在长耗时软件故障诊断、大规模代码重构与自动化运维（如 SWE-bench 场景）中，单次自主 Agent 的执行往往长达数小时乃至一整天。工程师在移动笔记本上发起任务时，常常受困于：
1. **物理设备强绑定**：合盖休眠、通勤移动或无线断网直接导致宿主进程与 Agent Event Loop 异常崩溃；
2. **认知状态不可转移**：传统终端工具（如 SSH/Tmux）仅能维持字节流，无法持久化或移交 Agent 的规划树、因果记忆、当前假设与局部变量；
3. **协作交接高摩擦**：移交他人或轮班 Agent 时需重新从头提示，浪费算力且易状态脱节。

**关键洞察**：绝大多数运维与云端长程任务，其操作目标（Target Environment，如 VPS、集群）天然驻留在云端。被死锁在笔记本上的仅仅是 **Agent 的认知与执行上下文**。

本项目提出并实现了 **上下文转移范式 (Context Handoff Paradigm, CHP)**，将任务执行彻底解耦为：
- **目标与环境面 (Target Environment Plane)**
- **认知与状态面 (Cognitive State Plane)**
- **控制与执行面 (Control & Execution Plane)**

---

## 2. 成果概览与交付清单

本项目已按照 AI 项目启动包标准规范完成完整落地与验证：

- 📄 **正式学术报告**: [`paper/main.pdf`](paper/main.pdf)（基于 Typst 编译的双栏标准 Preprint 报告，含数学建模、系统架构图与全流程接力实验指标）
- 💻 **核心框架源码**: [`code/chp/`](code/chp/)（零依赖、轻量级的协议模型、状态中继与租约锁、断点感知 Worker 执行器与交接便签生成器）
- 🖥️ **双端接力仿真**: [`code/demo_laptop.py`](code/demo_laptop.py) 与 [`code/demo_desktop.py`](code/demo_desktop.py)
- 🌐 **交互式 Web 控制台**: [`code/web_demo.py`](code/web_demo.py)（纯标准库实现的三列可视化接力面板，运行于 `http://localhost:8765`）
- 📦 **真实上下文切片数据**: [`data/task-vps-502-recovery.bundle.json`](data/task-vps-502-recovery.bundle.json)
- 📊 **测试与评测记录**: [`results/README.md`](results/README.md)
- 🧪 **自动化测试套件**: [`code/test_chp.py`](code/test_chp.py)（单元与集成测试 100% 通过）

---

## 3. 系统架构与三层解耦模型

```
+-----------------------------------------------------------------------------------+
| 1. 目标与环境面 (Target Environment Plane)                                        |
|    远程生产基础设施 (Cloud VPS / Nginx / PHP-FPM / Microservices)                |
+-----------------------------------------------------------------------------------+
                                    ▲                                 ▲
                          (阶段1-2排障)                             (阶段3-5热修)
                                    │                                 │
+-----------------------------------------------------------------------------------+
| 2. 认知与状态面 (Cognitive State Plane) - 统一状态中继 (Relay)                    |
|    - Cognitive State: Goal • Plan Tree • Working Memory Facts                     |
|    - Handover Note: 已掌握事实 • 故障根因 • 建议下一步                            |
|    - Runtime Checkpoint: Step Index • Variables • Distributed Lease Lock          |
+-----------------------------------------------------------------------------------+
               ▲                                                       │
         (一键挂起 Handoff)                                      (一键接管 Resume)
               │                                                       ▼
+------------------------------------+    +-----------------------------------------+
| 3. 发起端 Worker                   |    | 3. 接管端 Worker                         |
|    💻 笔记本 (Laptop-ThinkPad)     |    |    🖥️ 台式机 (Desktop-Workstation)       |
+------------------------------------+    +-----------------------------------------+
```

---

## 4. 快速复现与使用指南

### ① 运行单元与端到端测试
```powershell
python code/test_chp.py
```
验证上下文快照序列化无损性、多设备排他租约锁与完整的 Handoff/Resume 管道。

### ② 命令行双设备接力演示
- **步骤 1：笔记本端发起长程任务**（执行前 2 步排查并挂起）：
  ```powershell
  python code/demo_laptop.py
  ```
  *日志输出提示任务已安全暂存，包含已掌握事实（定位到 PHP-FPM OOM 崩溃），电脑可直接合盖断网。*
- **步骤 2：台式机端一键接管**（扫描中继并续跑）：
  ```powershell
  python code/demo_desktop.py
  ```
  *自动检测到挂起任务并打印交接便签，直接从第 3 步开始配置热修并验证服务恢复。*

### ③ 交互式 Web 控制台
```powershell
python code/web_demo.py
```
在浏览器中打开 `http://localhost:8765`：
- 左侧点击 **[🚀 发起任务]** 查看笔记本执行进度；
- 点击 **[⏸️ 一键转交 (Handoff)]** 观察中枢即时生成交接卡片；
- 右侧点击 **[✨ 一键接管并完成 (Resume)]** 观察台式机秒级接管续跑完成闭环。

### ④ 本地报告重新编译
```powershell
.\scripts\build-local.ps1
```
自动调用 Typst 重新编译 `paper/main.typ` 生成 `paper/main.pdf` 并渲染页面预览。

---

## 5. 核心实验指标

| 评测指标 | 测量结果 | 传统对比与优势 |
| :--- | :--- | :--- |
| **状态序列化保真度** | **100%** | 规划树、中间事实与变量无损还原 |
| **快照文件大小** | **~3.5 KB** | 相比容器/虚拟机快照（100MB~10GB）降低五个数量级 |
| **落盘与加载延迟** | **落盘 < 5ms, 恢复 < 12ms** | 毫秒级接管，接管端即刻具备完整任务认知 |
| **并发竞态防护** | **带 TTL 租约锁 100% 互斥** | 杜绝跨设备协同“脑裂”与并发写冲突 |

---

## 6. 引用

```bibtex
@article{sherlock2026contexthandoff,
  title={Context Handoff Paradigm: Decoupling Cognitive State and Target Environment for Long-running Autonomous Agents},
  author={Sherlock, H. and Rumu, J. and Dave, W.},
  year={2026}
}
```
