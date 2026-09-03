# 数据与上下文切片说明 (Data & Context Bundles)

本目录存放上下文转移范式 (Context Handoff Paradigm, CHP) 的核心数据模型样本、上下文切片（Context Bundles）及测试追踪数据。

## 数据文件清单

- `task-vps-502-recovery.bundle.json`:
  真实长程运维任务在执行到第 2 步后安全挂起并生成的上下文快照。包含：
  - `target_env`: 目标环境规格（解耦的 VPS 连接参数与工作目录）
  - `cognitive_state`: Agent 的规划列表、已验证事实（Memory）、交互历史
  - `checkpoint`: 当前断点游标与局部变量表
  - `handover_note`: 自动提炼的高层交接便签

## 数据结构字段定义
详见 [`code/chp/protocol.py`](../code/chp/protocol.py) 中的 `ContextBundle` 类定义。
